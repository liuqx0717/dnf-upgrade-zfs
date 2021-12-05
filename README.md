# Auto upgrade ZFS packages on Fedora

Installing OpenZFS on Fedora is easy ([instructions](
https://openzfs.github.io/openzfs-docs/Getting%20Started/Fedora/index.html)),
but *upgrading* the packages can be cumbersome.

The ZFS kernel modules are managed by dkms on Fedora. Sometimes running `dnf
upgrade` may cause issues, because the newest kernel on Fedora might be not
yet supported by OpenZFS. Also it's suggested that zfs packages should be
upgraded *before* kernel upgrades (see [this comment on GitHub](
https://github.com/openzfs/zfs/issues/9891#issuecomment-761979624)).

This little script is designed to eliminate all the laborious manual work and
do the upgrades **just in one shot**.

## Steps involved in this script

1. If zfs *can* be upgraded, run `dnf upgrade zfs*`.
2. If the target kernel version is not supported by the newest zfs package
   available on this system, run `dnf --exclude=kernel* upgrade`; otherwise
   run `dnf upgrade`.

The max kernel version supported by OpenZFS is retrieved from this link:

```
https://raw.githubusercontent.com/openzfs/zfs/zfs-<version>/META
```

dkms/dracut will be automatically invoked when installing/removing a kernel.
See these hooks:

```
/etc/kernel/install.d/dkms
/usr/lib/kernel/install.d/40-dkms.install
/usr/lib/kernel/install.d/50-dracut.install
```

## Usage

```
usage: dnf-upgrade-zfs.py [OPTIONS] [-- DNFOPTS...]

positional arguments:
  DNFOPTS        additional options for dnf, e.g. dnf-upgrade-zfs.py -- -y

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  verbose mode

```

Examples:

```
# By default the user's confirmation is required before doing any upgrades
sudo ./dnf-upgrade-zfs.py

# Do the upgrades directly (by passing -y to dnf)
sudo ./dnf-upgrade-zfs.py -- -y
```

## Compatibility

Tested on Fedora 34. But it should work on any distro with `dnf` (e.g. CentOS).
