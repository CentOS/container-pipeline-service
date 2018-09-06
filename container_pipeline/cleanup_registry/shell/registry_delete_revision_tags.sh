#!/usr/bin/env bash

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

REGISTRY_STORAGE=${REGISTRY_STORAGE:-"/var/lib/registry"}
REGISTRY_REPOSITORIES="${REGISTRY_STORAGE}/registry/v2/repositories/";
MANIFEST_LIST="/tmp/registry_manifests.txt"

pushd ${REGISTRY_REPOSITORIES}

echo "Searching for revision tags to remove ... ";

MANIFESTS_WITHOUT_TAGS=$(comm -23 <(find . -type f -name "link" | grep "_manifests/revisions/sha256" | grep -v "\/signatures\/sha256\/" | awk -F/ '{print $(NF-1)}' | sort) <(for f in $(find . -type f -name "link" | grep "_manifests/tags/.*/current/link"); do cat ${f} | sed 's/^sha256://g'; echo; done | sort))
find . > ${MANIFEST_LIST};

echo "Finding and removing all occourences of the manifests ... ";
echo "";

for manifest in ${MANIFESTS_WITHOUT_TAGS}; do
    repos=$(grep "_manifests/revisions/sha256/${manifest}/link" ${MANIFEST_LIST} | awk -F "_manifest"  '{print $(NF-1)}' | sed 's#^./\(.*\)/#\1#');
    for repo in ${repos}; do
        echo "Deleting manifest repo ${repo}";
        rm -rf "${repo}/_manifests/revisions/sha256/${manifest}";
    done
done

popd;


