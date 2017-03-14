import json
import rpmUtils.arch
import yum
from distutils.version import LooseVersion


class YumRepoUpdateCheck(yum.YumBase):
    """
    Check Yum repos for updates.
    """

    def __init__(self, repo_id, baseurls, arch='x86_64'):
        """
        Args:
            repo_id (str): Repo id
            baseurls (list): A list of upstream repo links
            archlist (list): A list of arch strings
        """
        super(YumRepoUpdateCheck, self).__init__()
        self.baseurls = baseurls
        self.repo_id = repo_id
        self.yruc_basecachedir = yum.misc.getCacheDir()
        self.setCacheDir(self.yruc_basecachedir)
        self.archlist = [arch]

    def setup_repos(self):
        """
        Setup repos for upstream repos and retrieve repo data.
        """
        for n, baseurl in enumerate(self.baseurls):
            repo_id = '%s%s' % (self.repo_id, n + 1)

            # create new repo object
            repo = yum.yumRepo.YumRepository(repo_id)
            repo.name = repo_id
            if baseurl.startswith('mirror:'):
                repo.mirrorlist = baseurl[len('mirror:'):]
            elif baseurl.find('mirrorlist') >= 0:
                repo.mirrorlist = baseurl
            elif baseurl.startswith('/'):
                repo.baseurl = ['file:' + baseurl]
            else:
                repo.baseurl = [baseurl]
            repo.basecachedir = self.yruc_basecachedir
            repo.base_persistdir = self.yruc_basecachedir
            repo.metadata_expire = 0
            repo.timestamp_check = False

            # add repo to the list of repos
            self.repos.add(repo)
            # enable repo
            self.repos.enableRepo(repo_id)
            self.doRepoSetup(thisrepo=repo_id)

            if '*' in self.archlist:
                archs = rpmUtils.arch.arches
                archlist = list(set(archs.keys()).union(set(archs.values())))
            else:
                archlist = self.archlist

            # load sacks for the repo
            self._getSacks(archlist=archlist, thisrepo=repo_id)

    def iter_newest_packages(self):
        pkgs = sorted(self.pkgSack.returnPackages())
        last_new_pkg = None
        for pkg in pkgs:
            if last_new_pkg:
                if pkg.name == last_new_pkg.name:
                    if LooseVersion(pkg.version) > LooseVersion(
                            last_new_pkg.version):
                        last_new_pkg = pkg
                    elif LooseVersion(pkg.version) == LooseVersion(
                        last_new_pkg.version) \
                            and LooseVersion(pkg.release) > LooseVersion(
                                last_new_pkg.release):
                        last_new_pkg = pkg
                else:
                    yield last_new_pkg
                    last_new_pkg = pkg
            else:
                last_new_pkg = pkg
        yield last_new_pkg

    def compare(self, opkgs, npkgs):
        """
        Compare new pkg data with old ones

        Args:
            opkgs: Sorted list of pkg tuple
            npkgs: Sorted list of pkg tuple
        """
        opkg = None
        # old index
        oi = 0

        modified = []
        added = []
        removed = []

        len_opkgs = len(opkgs)

        for pkg in npkgs:
            if len_opkgs == 0:
                added.append((None, pkg))
                continue
            n, a, e, v, r = opkg = opkgs[oi]
            _n, _a, _e, _v, _r = pkg
            while n < _n:
                removed.append((opkg, None))
                oi += 1
                n, a, e, v, r = opkgs[oi]
            if n > _n:
                added.append((None, pkg))
            elif n == _n:
                oi += 1
                if _v != v or _r != r:
                    modified.append((opkg, pkg))
        while oi < len_opkgs:
            removed.append((opkgs[oi], None))
            oi += 1
        return (added, modified, removed)


def main():
    baseurls = [
        'http://mirror.centos.org/centos/7.3.1611/os/x86_64/',
        'http://mirror.centos.org/centos/7.3.1611/updates/x86_64/'
    ]
    yruc = YumRepoUpdateCheck('upstream', baseurls, 'x86_64')
    yruc.setup_repos()
    try:
        with open('repodata.json') as f:
            opkgs = json.load(f)
    except:
        opkgs = []
    npkgs = [pkg.pkgtup for pkg in yruc.iter_newest_packages()]
    added, modified, removed = yruc.compare(opkgs, npkgs)

    print 'Added: {}, Modified: {}, Removed: {}'.format(
        len(added), len(modified), len(removed))

    with open('repodata.json', 'w') as f:
        json.dump(npkgs, f, indent=2)


if __name__ == '__main__':
    main()
