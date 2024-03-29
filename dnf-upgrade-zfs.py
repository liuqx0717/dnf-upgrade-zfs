#!/usr/bin/env python3
import packaging.version as version
import requests
import re
import logging
import dnf
import subprocess
import sys
import argparse

LOGLEVEL = logging.INFO
LOGFMT = "[%(levelname)s] %(name)s: %(message)s"
DNFOPTS = []
logger = logging.getLogger(__name__)
dnfBase = dnf.Base()
proxies = {}


def getZfsMaxKernelVer(zfs_ver):
    """
    Get the max Linux kernel version supported by ZFS.
    @zfs_ver: version.Version
    @return: version.Version
    """
    url = "https://raw.githubusercontent.com/openzfs/zfs/zfs-%s/META" % \
          (str(zfs_ver), )
    logger.debug("Getting zfsMetaStr from '%s'...", url)
    resp = requests.get(url, timeout=10, proxies=proxies)
    zfsMetaStr = resp.text
    logger.debug("zfsMetaStr=%s", repr(zfsMetaStr))
    findRes = re.findall(r"^Linux-Maximum:\s*(\d+\.\d+)$",
                         zfsMetaStr, re.MULTILINE)
    if len(findRes) != 1:
        raise ValueError("len(findRes) should be 1. findRes=%s, zfsMetaStr=%s" % \
                         (repr(findRes), repr(zfsMetaStr)))
    zfsMaxKernelVer = version.Version(findRes[0])
    logger.info("zfsMaxKernelVer=%s", str(zfsMaxKernelVer))
    return zfsMaxKernelVer


def dnfQueryToMap(query):
    """
    Convert a dnf.query.Query to map. Key: name; val: [dnf.package.Package]."
    """
    ret = {}
    for p in query:
        ret.setdefault(p.name, []).append(p)
    logger.debug("Query result: %s", repr(ret))
    return ret


def getInstalledPkgVer(pkgName):
    """
    Get the versions of a package currently installed on the system.
    @pkgName: string
    @return: an array of version.Version.
    """
    query = dnfBase.sack.query().installed().filter(name=pkgName)
    m = dnfQueryToMap(query)
    assert len(m) == 1
    pkgs = m[pkgName]
    ret = [version.Version(p.version) for p in pkgs]
    logger.info("Installed versions of '%s': %s",
                pkgName, repr([str(v) for v in ret]))
    return ret


def getTargetPkgVer(pkgName):
    """
    Get the target version of a package in a dnf upgrade operation.
    When multiple target versions are available, return the biggest one.
    @pkgName: string
    @return: version.Version. (Or None if no upgrade is needed.)
    """
    ret = None
    query = dnfBase.sack.query().upgrades().filter(name=pkgName)
    m = dnfQueryToMap(query)
    if len(m) == 0:
        logger.info("Target version of '%s': %s", pkgName, str(ret))
        return ret
    assert len(m) == 1
    pkgs = m[pkgName]
    versions = [version.Version(p.version) for p in pkgs]
    ret = max(versions)
    logger.info("Target version of '%s': %s", pkgName, str(ret))
    return ret


def cmpMajorMinor(v1, v2):
    """
    Compare major and minor version of two version.Version objects.
    @return: -1 if v1 > v2, 0 if v1 == v2, 1 if v1 < v2.
    """
    a = [v1.major, v1.minor]
    b = [v2.major, v2.minor]
    if a < b:
        return 1
    elif a > b:
        return -1
    return 0


def runCommand(args):
    """
    Run a command, wait until the command completes while the user can
    interact with it (inherit stdin/stdout/stderr of current process).
    @args: command line args, e.g. ["dnf", "--exclude=kernel*", "upgrade"].
    @return: error code.
    """
    logger.debug("Executing command %s ...", repr(args))
    rc = subprocess.call(args)
    logger.debug("Finished command %s, rc=%d", repr(args), rc)
    return rc


def runDnfCommand(args):
    """
    Run a dnf command, prepend @args with DNFOPTS.
    @args: dnf command line args, e.g. ["--exclude=kernel*", "upgrade"].
    @return: error code.
    """
    return runCommand(["/bin/dnf"] + DNFOPTS + args)


def initLogger(logLevel, logFmt):
    logger.setLevel(logLevel)
    loggerHandler = logging.StreamHandler()
    loggerHandler.setFormatter(logging.Formatter(logFmt))
    logger.addHandler(loggerHandler)


def initDnf(logLevel, logFmt):
    logger.info("Initializing dnf...")
    dnfLogger = logging.getLogger("dnf")
    dnfLogger.setLevel(logLevel)
    dnfLoggerHandler = logging.StreamHandler()
    dnfLoggerHandler.setFormatter(logging.Formatter(logFmt))
    dnfLogger.addHandler(dnfLoggerHandler)
    dnfBase.conf.read(dnfBase.conf.config_file_path)
    logger.debug("dnf proxy: %s", dnfBase.conf.proxy)
    dnfBase.read_all_repos()
    for repo in dnfBase.repos.iter_enabled():
        logger.debug("Enabled repo: %s, %s, %s", str(repo.id),
                     str(repo.baseurl), str(repo.metalink))
    dnfBase.fill_sack(load_system_repo=True, load_available_repos=True)
    logger.info("Successfully initialized dnf")


def initProxies(proxyUrl=""):
    """
    @proxyUrl: e.g. "socks5h://127.0.0.1:8080". See the curl man page
        for details.
    """
    global proxies
    logger.debug("Script proxy: %s", proxyUrl)
    if not proxyUrl:
        return
    proxies = {
        "http": proxyUrl,
        "https": proxyUrl,
    }


def main():
    # Get zfs/kernel versions
    zfsTargetVer = getTargetPkgVer("zfs")
    zfsInstalledVer = getInstalledPkgVer("zfs")
    zfsMaxAvailVer = max(zfsInstalledVer)
    if zfsTargetVer:
        assert zfsTargetVer > zfsMaxAvailVer
        zfsMaxAvailVer = zfsTargetVer
    zfsMaxKernelVer = getZfsMaxKernelVer(zfsMaxAvailVer)
    krnTargetVer = getTargetPkgVer("kernel")

    # If we can upgrade zfs, do it now.
    if zfsTargetVer:
        logger.info("Upgrading zfs...")
        rc = runDnfCommand(["upgrade", "zfs*"])
        if rc != 0:
            logger.error("Failed to upgrade zfs, exiting. rc=%d", rc)
            return rc

    # Upgrade all the packages, excluding the kernel if necessary.
    dnfOpts = []
    if krnTargetVer and cmpMajorMinor(krnTargetVer, zfsMaxKernelVer) < 0:
        logger.info("Excluding kernel upgrades, because %s > %s",
                    str(krnTargetVer), str(zfsMaxKernelVer))
        dnfOpts.append("--exclude=kernel*")
    logger.info("Upgrading all the packages...")
    rc = runDnfCommand(dnfOpts + ["upgrade"])
    return rc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage='%(prog)s [OPTIONS] [-- DNFOPTS...]')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="verbose mode")
    parser.add_argument("-x", "--proxy", type=str, default="",
                        help="proxy url, e.g. 'socks5h://127.0.0.1:8080'. "
                             "See the curl man page for details. Note that "
                             "only requests initiated by this script are "
                             "affected by this option. For requests initiated "
                             "inside dnf, use the proxy= setting in dnf.conf.")
    parser.add_argument("DNFOPTS", nargs="*",
                        help="additional options for dnf, e.g. %(prog)s -- -y")
    args = parser.parse_args()

    if args.verbose:
        LOGLEVEL = logging.DEBUG
    DNFOPTS.extend(args.DNFOPTS)

    initLogger(LOGLEVEL, LOGFMT)
    initDnf(LOGLEVEL, LOGFMT)
    initProxies(args.proxy)
    rc = main()
    sys.exit(rc)
