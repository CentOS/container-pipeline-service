#!/usr/bin/env bash

REG_PATH="/var/lib/registry/docker/registry/v2/repositories/";
MANIFEST_LIST="/tmp/registry_manifests.txt"

pushd ${REG_PATH}

echo "Searching for revision tags to remove ... ";

MANIFESTS_WITHOUT_TAGS=$(comm -23 <(find . -type f -name "link" | grep "_manifests/revisions/sha256" | grep -v "\/signatures\/sha256\/" | awk -F/ '{print $(NF-1)}' | sort) <(for f in $(find . -type f -name "link" | grep "_manifests/tags/.*/current/link"); do cat ${f} | sed 's/^sha256://g'; echo; done | sort))
find . > ${MANIFEST_LIST};

echo "Finding and removing all occourences of the manifests ... ";

for manifest in ${MANIFESTS_WITHOUT_TAGS}; do
    repos=$(grep "_manifests/revisions/sha256/${manifest}/link" ${MANIFEST_LIST} | awk -F "_manifest"  '{print $(NF-1)}' | sed 's#^./\(.*\)/#\1#');
    for repo in ${repos}; do
        sudo rm -rf "${repo}/_manifests/revisions/sha256/${manifest}"
    done
done

popd;

