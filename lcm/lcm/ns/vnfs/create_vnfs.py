# Copyright 2016 [ZTE] and others.
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
import json
import logging
import traceback
import uuid
from threading import Thread

from lcm.ns.vnfs.const import VNF_STATUS, NFVO_VNF_INST_TIMEOUT_SECOND, INST_TYPE, INST_TYPE_NAME
from lcm.ns.vnfs.wait_job import wait_job_finish
from lcm.pub.database.models import NfPackageModel, NfInstModel, NSInstModel, VmInstModel, VNFFGInstModel
from lcm.pub.exceptions import NSLCMException
from lcm.pub.msapi.extsys import get_vnfm_by_id
from lcm.pub.msapi.resmgr import create_vnf, create_vnf_creation_info
from lcm.pub.msapi.vnfmdriver import send_nf_init_request
from lcm.pub.utils.jobutil import JOB_MODEL_STATUS, JobUtil, JOB_TYPE
from lcm.pub.utils.share_lock import do_biz_with_share_lock
from lcm.pub.utils.timeutil import now_time
from lcm.pub.utils.values import ignore_case_get

logger = logging.getLogger(__name__)


def prepare_create_params():
    nf_inst_id = str(uuid.uuid4())
    NfInstModel(nfinstid=nf_inst_id, status=VNF_STATUS.INSTANTIATING, create_time=now_time(),
                lastuptime=now_time()).save()
    job_id = JobUtil.create_job(INST_TYPE_NAME.VNF, JOB_TYPE.CREATE_VNF, nf_inst_id)
    JobUtil.add_job_status(job_id, 0, 'create vnf record in database.', 0)
    return nf_inst_id, job_id


class CreateVnfs(Thread):
    def __init__(self, data, nf_inst_id, job_id):
        super(CreateVnfs, self).__init__()
        self.data = data
        self.nf_inst_id = nf_inst_id
        self.job_id = job_id
        self.ns_inst_id = ''
        self.vnf_id = ''
        self.vnfd_id = ''
        self.ns_inst_name = ''
        self.nsd_model = ''
        self.vnf_inst_name = ''
        self.vnfm_inst_id = ''
        self.inputs = ''
        self.nf_package_info = ''
        self.vnfm_nf_inst_id = ''
        self.vnfm_job_id = ''
        self.vnfm_inst_name = ''

    def run(self):
        try:
            self.get_params()
            self.check_nf_name_exist()
            self.get_vnfd_id()
            self.check_nf_package_valid()
            self.send_nf_init_request_to_vnfm()
            self.send_get_vnfm_request_to_extsys()
            self.send_create_vnf_request_to_resmgr()
            self.wait_vnfm_job_finish()
            self.write_vnf_creation_info()
            self.save_info_to_db()
        except NSLCMException as e:
            self.vnf_inst_failed_handle(e.message)
        except Exception:
            logger.error(traceback.format_exc())
            self.vnf_inst_failed_handle('unexpected exception')

    def get_params(self):
        self.ns_inst_id = self.data['ns_instance_id']
        vnf_index = int(self.data['vnf_index']) - 1
        additional_vnf_info = self.data['additional_param_for_vnf'][vnf_index]
        self.vnf_id = ignore_case_get(additional_vnf_info, 'vnfProfileId')
        additional_param = ignore_case_get(additional_vnf_info, 'additionalParam')
        self.vnfm_inst_id = ignore_case_get(additional_param, 'vnfmInstanceId')
        self.inputs = json.loads(ignore_case_get(additional_param, 'inputs'))

    def check_nf_name_exist(self):
        is_exist = NfInstModel.objects.filter(nf_name=self.vnf_inst_name).exists()
        if is_exist:
            logger.error('The name of NF instance already exists.')
            raise NSLCMException('The name of NF instance already exists.')

    def get_vnfd_id(self):
        ns_inst_info = NSInstModel.objects.get(id=self.ns_inst_id)
        self.ns_inst_name = ns_inst_info.name
        self.nsd_model = json.loads(ns_inst_info.nsd_model)
        for vnf_info in self.nsd_model['vnfs']:
            if self.vnf_id == vnf_info['vnf_id']:
                self.vnfd_id = vnf_info['properties']['id']
                self.vnf_inst_name = vnf_info['properties']['name']
                return
        logger.error('Can not found vnf in nsd model')
        raise NSLCMException('Can not found vnf in nsd model')

    def check_nf_package_valid(self):
        nf_package_info = NfPackageModel.objects.filter(vnfdid=self.vnfd_id)
        if not nf_package_info:
            logger.info('NF package not exist.')
            raise NSLCMException('NF package not exist.')
        self.nf_package_info = nf_package_info[0]

    def send_nf_init_request_to_vnfm(self):
        self.vnfm_job_id, self.vnfm_nf_inst_id = send_nf_init_request(self.vnfm_inst_id, self.vnf_inst_name,
                                                                      self.nf_package_info.nfpackageid, self.vnfd_id,
                                                                      self.inputs)
        NfInstModel.objects.filter(nfinstid=self.nf_inst_id).update(mnfinstid=self.vnfm_nf_inst_id,
                                                                    nf_name=self.vnf_inst_name,
                                                                    vnf_id=self.vnf_id,
                                                                    package_id=self.nf_package_info.nfpackageid,
                                                                    vnfm_inst_id=self.vnfm_inst_id,
                                                                    ns_inst_id=self.ns_inst_id,
                                                                    version=self.nf_package_info.vnfversion,
                                                                    vendor=self.nf_package_info.vendor,
                                                                    input_params=json.JSONEncoder().encode(self.inputs),
                                                                    lastuptime=now_time())

    def send_get_vnfm_request_to_extsys(self):
        resp_body = get_vnfm_by_id(self.vnfm_inst_id)
        self.vnfm_inst_name = ignore_case_get(resp_body, 'name')

    def send_create_vnf_request_to_resmgr(self):
        data = {
            'nf_inst_id': self.nf_inst_id,
            'vnfm_nf_inst_id': self.vnfm_nf_inst_id,
            'vnf_inst_name': self.vnf_inst_name,
            'ns_inst_id': self.ns_inst_id,
            'ns_inst_name': self.ns_inst_name,
            'nf_inst_name': NSInstModel.objects.get(id=self.ns_inst_id).name,
            'vnfm_inst_id': self.vnfm_inst_id,
            'vnfm_inst_name': self.vnfm_inst_name,
            'vnfd_name': json.loads(self.nf_package_info.vnfdmodel)['metadata']['name'],
            'vnfd_id': self.vnfd_id,
            'job_id': self.job_id,
            'nf_inst_status': VNF_STATUS.INSTANTIATING,
            'vnf_type': json.loads(self.nf_package_info.vnfdmodel)['metadata']['vnf_type'],
            'nf_package_id': self.nf_package_info.nfpackageid,
        }
        create_vnf(data)

    def wait_vnfm_job_finish(self):
        ret = wait_job_finish(vnfo_job_id=self.job_id, vnfm_job_id=self.vnfm_job_id, progress_range=[10, 90],
                              timeout=NFVO_VNF_INST_TIMEOUT_SECOND)

        if ret != JOB_MODEL_STATUS.FINISHED:
            logger.error('VNF instantiation failed on VNFM side.')
            raise NSLCMException('VNF instantiation failed on VNFM side.')

    def write_vnf_creation_info(self):
        vm_inst_infos = VmInstModel.objects.filter(insttype=INST_TYPE.VNF, instid=self.nf_inst_id)
        data = {
            'nf_inst_id': self.nf_inst_id,
            'ns_inst_id': self.ns_inst_id,
            'vnfm_inst_id': self.vnfm_inst_id,
            'vms': [{'vmId': vm_inst_info.resouceid, 'vmName': vm_inst_info.vmname, 'vmStatus': 'ACTIVE'} for
                    vm_inst_info in vm_inst_infos]
        }
        create_vnf_creation_info(data)

    def save_info_to_db(self):
        do_biz_with_share_lock("set-vnflist-in-vnffginst-%s" % self.ns_inst_id, self.save_vnf_inst_id_in_vnffg)
        NfInstModel.objects.filter(nfinstid=self.nf_inst_id).update(status=VNF_STATUS.ACTIVE, lastuptime=now_time())
        JobUtil.add_job_status(self.job_id, 100, 'vnf instantiation success', 0)

    def vnf_inst_failed_handle(self, error_msg):
        logger.error('VNF instantiation failed, detail message: %s' % error_msg)
        NfInstModel.objects.filter(nfinstid=self.nf_inst_id).update(status=VNF_STATUS.FAILED,
                                                                    lastuptime=now_time())
        JobUtil.add_job_status(self.job_id, 255, 'VNF instantiation failed, detail message: %s' % error_msg, 0)

    def save_vnf_inst_id_in_vnffg(self):
        vnffgs = self.nsd_model['vnffgs']
        for vnffg in vnffgs:
            if self.vnf_id not in vnffg['members']:
                continue
            vnffg_inst_infos = VNFFGInstModel.objects.filter(vnffgdid=vnffg['vnffg_Id'], nsinstid=self.ns_inst_id)
            if not vnffg_inst_infos:
                logger.error('Vnffg instance not exist.')
                raise NSLCMException('Vnffg instance not exist.')
            vnf_list = vnffg_inst_infos[0].vnflist
            vnffg_inst_infos.update(vnf_list=vnf_list + ',' + self.nf_inst_id if vnf_list else self.nf_inst_id)