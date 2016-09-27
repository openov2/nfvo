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
import logging
import uuid

from lcm.pub.database.models import NSDModel, NSInstModel
from lcm.pub.exceptions import NSLCMException
from lcm.pub.utils.timeutil import now_time

logger = logging.getLogger(__name__)


class CreateNSService(object):
    def __init__(self, nsd_id, ns_name, description):
        self.nsd_id = nsd_id
        self.ns_name = ns_name
        self.description = description
        self.ns_inst_id = ''
        self.ns_package_id = ''

    def do_biz(self):
        self.check_nsd_valid()
        self.check_ns_inst_name_exist()
        self.create_ns_inst()
        return self.ns_inst_id

    def check_nsd_valid(self):
        ns_package_info = NSDModel.objects.filter(nsd_id=self.nsd_id)
        if not ns_package_info:
            raise NSLCMException("nsd not exists.")
        self.ns_package_id = ns_package_info[0].id

    def check_ns_inst_name_exist(self):
        is_exist = NSInstModel.objects.filter(name=self.ns_name).exists()
        if is_exist:
            raise NSLCMException("ns instance name has already existed.")

    def create_ns_inst(self):
        self.ns_inst_id = uuid.uuid4()
        NSInstModel(id=self.ns_inst_id, name=self.ns_name, nspackage_id=self.ns_package_id, nsd_id=self.nsd_id,
                    description=self.description, status='empty', lastuptime=now_time()).save()
