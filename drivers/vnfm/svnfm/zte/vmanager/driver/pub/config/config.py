# Copyright 2016 ZTE Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [MSB]
MSB_SERVICE_IP = '127.0.0.1'
MSB_SERVICE_PORT = '80'

# [register]
REG_TO_MSB_WHEN_START = True
REG_TO_MSB_REG_URL = "/openoapi/microservices/v1/services"
REG_TO_MSB_REG_PARAM = {
    "serviceName": "ztevmanagerdriver",
    "version": "v1",
    "url": "/openoapi/ztevmanagerdriver/v1",
    "protocol": "REST",
    "visualRange": "1",
    "nodes": [{
        "ip": "127.0.0.1",
        "port": "8410",
        "ttl": 0
    }]
}
