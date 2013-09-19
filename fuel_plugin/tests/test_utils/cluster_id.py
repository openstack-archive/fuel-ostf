#!/usr/bin/env python
# -*- coding: utf-8 -*-

from requests import get
import sys


def main():
    try:
        r = get('http://localhost:8000/api/clusters').json()
    except IOError or ValueError as e:
        print e.message
        return 1

    cluster_id = next(item['id'] for item in r)
    print cluster_id
    return 0

if __name__ == '__main__':
    sys.exit(main())


