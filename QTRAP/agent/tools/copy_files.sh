#!/usr/bin/env bash
set -euo pipefail

# Move files between the local machine and the cluster, or inspect a
# remote path. Remote paths are checked against REMOTE_BASE_DIR and
# refused if they resolve outside it. get/put/copy use -r, so they work
# on whole directories as well as single files.
#
# Inputs:
#   REMOTE_HOST, REMOTE_BASE_DIR (environment variables)
#   mode: get, put, cat, write, list, or copy, plus mode-specific arguments
#
# Outputs:
#   depends on mode -- a copied file or directory, printed file contents,
#   a new remote file, a directory listing, or a remote-to-remote copy

if [ -z "${REMOTE_HOST:-}" ]; then
    echo "Error: REMOTE_HOST is not set."
    exit 1
fi

if [ -z "${REMOTE_BASE_DIR:-}" ]; then
    echo "Error: REMOTE_BASE_DIR is not set."
    exit 1
fi

mode="${1:-}"

check_relative() {

    if [[ "$1" == /* || "$1" == *".."* ]]; then
        echo "Error: '$1' must be a relative path inside the project, with no '..' or leading '/'."
        exit 1
    fi

}

case "$mode" in
    get)
        if [ "$#" -lt 3 ]; then
            echo "Usage: $0 get <remote_relative_path> <local_dest>"
            exit 1
        fi

        remote_rel="$2"
        local_dest="$3"

        check_relative "$remote_rel"

        local_dir=$(dirname "$local_dest")
        mkdir -p "$local_dir"

        scp -r "$REMOTE_HOST:$REMOTE_BASE_DIR/$remote_rel" "$local_dest"
        ;;

    put)
        if [ "$#" -lt 3 ]; then
            echo "Usage: $0 put <local_path> <remote_relative_path>"
            exit 1
        fi

        local_path="$2"
        remote_rel="$3"

        check_relative "$remote_rel"

        remote_parent=$(dirname "$REMOTE_BASE_DIR/$remote_rel")
        ssh "$REMOTE_HOST" "mkdir -p $remote_parent"

        scp -r "$local_path" "$REMOTE_HOST:$REMOTE_BASE_DIR/$remote_rel"
        ;;

    cat)
        if [ "$#" -lt 2 ]; then
            echo "Usage: $0 cat <remote_relative_path>"
            exit 1
        fi

        remote_rel="$2"

        check_relative "$remote_rel"

        ssh "$REMOTE_HOST" "cat $REMOTE_BASE_DIR/$remote_rel"
        ;;

    write)
        if [ "$#" -lt 3 ]; then
            echo "Usage: $0 write <remote_relative_path> <content>"
            exit 1
        fi

        remote_rel="$2"
        content="$3"

        check_relative "$remote_rel"

        ssh "$REMOTE_HOST" "cat > $REMOTE_BASE_DIR/$remote_rel" <<< "$content"
        ;;

    list)
        if [ "$#" -lt 2 ]; then
            remote_rel="."
        else
            remote_rel="$2"
        fi

        check_relative "$remote_rel"

        ssh "$REMOTE_HOST" "ls -la $REMOTE_BASE_DIR/$remote_rel"
        ;;

    copy)
        if [ "$#" -lt 3 ]; then
            echo "Usage: $0 copy <remote_src_relative> <remote_dest_relative>"
            exit 1
        fi

        src_rel="$2"
        dest_rel="$3"

        check_relative "$src_rel"
        check_relative "$dest_rel"

        dest_dir=$(dirname "$REMOTE_BASE_DIR/$dest_rel")

        ssh "$REMOTE_HOST" "mkdir -p $dest_dir && cp -r $REMOTE_BASE_DIR/$src_rel $REMOTE_BASE_DIR/$dest_rel"
        ;;

    *)
        echo "Usage:"
        echo "  $0 get <remote_relative_path> <local_dest>"
        echo "  $0 put <local_path> <remote_relative_path>"
        echo "  $0 cat <remote_relative_path>"
        echo "  $0 write <remote_relative_path> <content>"
        echo "  $0 list <remote_relative_dir>"
        echo "  $0 copy <remote_src_relative> <remote_dest_relative>"
        exit 1
        ;;
esac