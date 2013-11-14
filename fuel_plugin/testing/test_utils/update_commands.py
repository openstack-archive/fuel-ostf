#    Copyright 2013 Mirantis, Inc.
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


from json import loads, dumps


def main():
    with open('fuel_plugin/ostf_adapter/commands.json', 'rw+') as commands:
        data = loads(commands.read())
        for item in data:
            if 'argv' in data[item] and item in ['fuel_sanity', 'fuel_smoke']:
                if "--with-xunit" not in data[item]['argv']:
                    data[item]['argv'].extend(
                        ["--with-xunit",
                         '--xunit-file={0}.xml'.format(item)]
                    )

            elif item in ['fuel_sanity', 'fuel_smoke']:
                data[item]['argv'] = ["--with-xunit", ]

        test_apps = {
            "plugin_general": {
                "test_path": ("fuel_plugin/tests/functional/"
                              "dummy_tests/general_test.py"),
                "driver": "nose"
            },
            "plugin_stopped": {
                "test_path": ("fuel_plugin/tests/functional/"
                              "dummy_tests/stopped_test.py"),
                "driver": "nose"
            }
        }

        if 'plugin_general' not in data or 'plugin_stopped' not in data:
            data.update(test_apps)
        commands.seek(0)
        commands.write(dumps(data))
        commands.truncate()

if __name__ == '__main__':
    main()
