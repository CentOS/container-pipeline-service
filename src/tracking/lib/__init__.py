def get_navr_from_pkg_name(pkg):
    a, b = pkg.rsplit('-', 1)
    name, version = a.rsplit('-', 1)
    try:
        release, arch = b.rsplit('.', 1)
    except ValueError:
        release, arch = b, ''

    return (name, arch, version, release)
