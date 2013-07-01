# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import json
import time
import urllib

from fuel_health.common.rest_client import RestClient
from fuel_health import exceptions


class ImagesClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ImagesClientJSON, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.compute.catalog_type
        self.build_interval = self.config.compute.build_interval
        self.build_timeout = self.config.compute.build_timeout

    def create_image(self, server_id, name, meta=None):
        """Creates an image of the original server."""

        post_body = {
            'createImage': {
                'name': name,
            }
        }

        if meta is not None:
            post_body['createImage']['metadata'] = meta

        post_body = json.dumps(post_body)
        resp, body = self.post('servers/%s/action' % str(server_id),
                               post_body, self.headers)
        return resp, body

    def _image_meta_to_headers(self, fields):
        headers = {}
        fields_copy = copy.deepcopy(fields)
        copy_from = fields_copy.pop('copy_from', None)
        if copy_from is not None:
            headers['x-glance-api-copy-from'] = copy_from
        for key, value in fields_copy.pop('properties', {}).iteritems():
            headers['x-image-meta-property-%s' % key] = str(value)
        for key, value in fields_copy.pop('api', {}).iteritems():
            headers['x-glance-api-property-%s' % key] = str(value)
        for key, value in fields_copy.iteritems():
            headers['x-image-meta-%s' % key] = str(value)
        return headers

    def _create_with_data(self, headers, data):
        resp, body_iter = self.http.raw_request('POST', '/v1/images',
                                                headers=headers, body=data)
        self._error_checker('POST', '/v1/images', headers, data, resp,
                            body_iter)
        body = json.loads(''.join([c for c in body_iter]))
        return resp, body['image']

    def create_image_by_file(self, name, container_format, disk_format, **kwargs):
        """
        Create a test image based on located file.
        """
        params = {
            "name": name,
            "container_format": container_format,
            "disk_format": disk_format,
        }

        headers = {}

        for option in ['is_public', 'location', 'properties',
                       'copy_from', 'min_ram']:
            if option in kwargs:
                params[option] = kwargs.get(option)

        headers.update(self._image_meta_to_headers(params))

        if 'data' in kwargs:
            return self._create_with_data(headers, kwargs.get('data'))

        resp, body = self.post('v1/images', None, headers)
        body = json.loads(body)
        return resp, body['image']

    def list_images(self, params=None):
        """Returns a list of all images filtered by any parameters."""
        url = 'images'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def list_images_with_detail(self, params=None):
        """Returns a detailed list of images filtered by any parameters."""
        url = 'images/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['images']

    def get_image(self, image_id):
        """Returns the details of a single image."""
        resp, body = self.get("images/%s" % str(image_id))
        body = json.loads(body)
        return resp, body['image']

    def delete_image(self, image_id):
        """Deletes the provided image."""
        return self.delete("images/%s" % str(image_id))

    def wait_for_image_resp_code(self, image_id, code):
        """
        Waits until the HTTP response code for the request matches the
        expected value
        """
        resp, body = self.get("images/%s" % str(image_id))
        start = int(time.time())

        while resp.status != code:
            time.sleep(self.build_interval)
            resp, body = self.get("images/%s" % str(image_id))

            if int(time.time()) - start >= self.build_timeout:
                raise exceptions.TimeoutException

    def wait_for_image_status(self, image_id, status):
        """Waits for an image to reach a given status."""
        resp, image = self.get_image(image_id)
        start = int(time.time())

        while image['status'] != status:
            time.sleep(self.build_interval)
            resp, image = self.get_image(image_id)

            if image['status'] == 'ERROR':
                raise exceptions.AddImageException(image_id=image_id)

            if int(time.time()) - start >= self.build_timeout:
                raise exceptions.TimeoutException

    def list_image_metadata(self, image_id):
        """Lists all metadata items for an image."""
        resp, body = self.get("images/%s/metadata" % str(image_id))
        body = json.loads(body)
        return resp, body['metadata']

    def set_image_metadata(self, image_id, meta):
        """Sets the metadata for an image."""
        post_body = json.dumps({'metadata': meta})
        resp, body = self.put('images/%s/metadata' % str(image_id),
                              post_body, self.headers)
        body = json.loads(body)
        return resp, body['metadata']

    def update_image_metadata(self, image_id, meta):
        """Updates the metadata for an image."""
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('images/%s/metadata' % str(image_id),
                               post_body, self.headers)
        body = json.loads(body)
        return resp, body['metadata']

    def get_image_metadata_item(self, image_id, key):
        """Returns the value for a specific image metadata key."""
        resp, body = self.get("images/%s/metadata/%s" % (str(image_id), key))
        body = json.loads(body)
        return resp, body['meta']

    def set_image_metadata_item(self, image_id, key, meta):
        """Sets the value for a specific image metadata key."""
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('images/%s/metadata/%s' % (str(image_id), key),
                              post_body, self.headers)
        body = json.loads(body)
        return resp, body['meta']

    def delete_image_metadata_item(self, image_id, key):
        """Deletes a single image metadata key/value pair."""
        resp, body = self.delete("images/%s/metadata/%s" %
                                 (str(image_id), key))
        return resp, body

    def is_resource_deleted(self, id):
        try:
            self.get_image(id)
        except exceptions.NotFound:
            return True
        return False
