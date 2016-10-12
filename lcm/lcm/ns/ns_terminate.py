# coding=utf-8
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
import math
import traceback
import logging
import json

from lcm.pub.utils.restcall import req_by_msb
from lcm.ns.vnfs.wait_job import wait_job_finish
from lcm.pub.database.models import NSInstModel, VLInstModel, FPInstModel, NfInstModel
from lcm.pub.utils.jobutil import JOB_MODEL_STATUS, JobUtil
from lcm.pub.exceptions import NSLCMException

# [delete vnf try times]

logger = logging.getLogger(__name__)


class TerminateNsService(object):
    def __init__(self, ns_inst_id, terminate_type, terminate_timeout, job_id):
        self.ns_inst_id = ns_inst_id
        self.terminate_type = terminate_type
        self.terminate_timeout = terminate_timeout
        self.job_id = job_id
        self.vnfm_inst_id = ''

    def do_biz(self):
        self.check_data()

        if self.cancel_sfc_list() == 'false':
            raise NSLCMException("delete sfc error")

        self.cancel_vnf_list()

        if self.cancel_vl_list() == 'false':
            raise NSLCMException("delete vl error")

        self.finaldata()

    def check_data(self):
        JobUtil.add_job_status(self.job_id, 0, "TERMINATING...", '')
        ns_inst = NSInstModel.objects.filter(id=self.ns_inst_id)
        if not ns_inst.exists():
            logger.error('ns instance [%s] is not exist.' % self.ns_inst_id)
            raise NSLCMException('ns instance [%s] is not exist.' % self.ns_inst_id)
        JobUtil.add_job_status(self.job_id, 10, "Ns cancel: check ns_inst_id success", '')
        return ns_inst[0]

    # 删除VLINST
    def cancel_vl_list(self):
        array_vlinst = VLInstModel.objects.filter(ownertype='2', ownerid=self.ns_inst_id)
        if not array_vlinst:
            logger.error("[cancel_vl_list] no vlinst attatch to ns_inst_id:%s" % self.ns_inst_id)
            return
        step_progress = 20 / len(array_vlinst)
        cur_progress = 70
        for vlinst in array_vlinst:

            # 删除逻辑平面后 删除VL实例
            # 终止VL实例
            tmp_msg = vlinst.vlinstanceid
            try:
                ret = self.delete_vl(tmp_msg)
                if ret[0] == 0:
                    cur_progress += step_progress
                    result = json.JSONDecoder().decode(ret[1]).get("result", "")
                    if result == '1':
                        JobUtil.add_job_status(self.job_id, cur_progress, "Delete vlinst:[%s] success." % tmp_msg, '')
                    else:
                        JobUtil.add_job_status(self.job_id, cur_progress, "Delete vlinst:[%s] failed." % tmp_msg, '')
                        return 'false'
                else:
                    NSInstModel.objects.filter(id=self.ns_inst_id).update(status='FAILED')
                    return 'false'
            except Exception as e:
                logger.error("[cancel_vl_list] error[%s]!" % e.message)
                logger.error(traceback.format_exc())
                JobUtil.add_job_status(self.job_id, cur_progress, "Delete vlinst:[%s] Failed." % tmp_msg, '')
                return 'false'
        return 'true'

    # 删除SFC
    def cancel_sfc_list(self):
        array_sfcinst = FPInstModel.objects.filter(nsinstid=self.ns_inst_id)
        if not array_sfcinst:
            logger.error("[cancel_sfc_list] no sfcinst attatch to ns_inst_id:%s" % self.ns_inst_id)
            return
        step_progress = 20 / len(array_sfcinst)
        cur_progress = 30
        for sfcinst in array_sfcinst:

            # 删除逻辑平面后 删除SFC实例
            # 终止SFC实例
            tmp_msg = sfcinst.sfcid
            try:
                ret = self.delete_sfc(tmp_msg)
                if ret[0] == 0:
                    cur_progress += step_progress
                    result = json.JSONDecoder().decode(ret[1]).get("result", "")
                    if result == '1':
                        JobUtil.add_job_status(self.job_id, cur_progress, "Delete sfcinst:[%s] success." % tmp_msg, '')
                    else:
                        JobUtil.add_job_status(self.job_id, cur_progress, "Delete sfcinst:[%s] failed." % tmp_msg, '')
                        return 'false'
                else:
                    NSInstModel.objects.filter(id=self.ns_inst_id).update(status='FAILED')
                    return 'false'
            except Exception as e:
                logger.error("[cancel_sfc_list] error[%s]!" % e.message)
                logger.error(traceback.format_exc())
                JobUtil.add_job_status(self.job_id, cur_progress, "Delete sfcinst:[%s] Failed." % tmp_msg, '')
                return 'false'
        return 'true'

    # 删除Vnf
    def cancel_vnf_list(self):
        array_vnfinst = NfInstModel.objects.filter(ns_inst_id=self.ns_inst_id)
        if not array_vnfinst:
            logger.error("[cancel_vnf_list] no vnfinst attatch to ns_inst_id:%s" % self.ns_inst_id)
            return
        step_progress = 20 / len(array_vnfinst)
        cur_progress = 50
        for vnfinst in array_vnfinst:

            # 删除逻辑平面后 删除VNF实例
            # 终止VNF实例
            tmp_msg = vnfinst.nfinstid
            try:
                self.delete_vnf(tmp_msg)
                cur_progress += step_progress
                JobUtil.add_job_status(self.job_id, cur_progress, "Delete vnfinst:[%s] success." % tmp_msg, '')
            except Exception as e:
                logger.error("[cancel_vnf_list] error[%s]!" % e.message)
                logger.error(traceback.format_exc())
                JobUtil.add_job_status(self.job_id, cur_progress, "Delete vnfinst:[%s] Failed." % tmp_msg, '')
                return 'false'
        return 'true'

    def delete_vnf(self, nf_instid):
        ret = self.call_vnfm_to_cancel_resource('vnf', nf_instid)
        self.delete_resource(ret)

    def delete_sfc(self, sfc_instid):
        ret = self.call_vnfm_to_cancel_resource('sfc', sfc_instid)
        return ret

    def delete_vl(self, vl_instid):
        ret = self.call_vnfm_to_cancel_resource('vl', vl_instid)
        return ret

    def delete_resource(self, result):
        if result[0] == 0:
            vnfm_job_id = json.JSONDecoder().decode(result[1]).get("jobid", "")
            self.add_progress(5, "SEND_TERMINATE_REQ_SUCCESS")
            if self.terminate_type == 'forceful':
                ret = wait_job_finish(self.vnfm_inst_id, self.job_id, vnfm_job_id,
                                      progress_range=[10, 50],
                                      timeout=self.terminate_timeout,
                                      job_callback=TerminateNsService.wait_job_mode_callback, mode='1')
                if ret != JOB_MODEL_STATUS.FINISHED:
                    logger.error('[NS terminate] VNFM terminate ns failed')
                    NSInstModel.objects.filter(id=self.ns_inst_id).update(status='FAILED')
                    raise NSLCMException("DELETE_NS_RESOURCE_FAILED")
        else:
            logger.error('[NS terminate] VNFM terminate ns failed')
            NSInstModel.objects.filter(id=self.ns_inst_id).update(status='FAILED')
            raise NSLCMException("DELETE_NS_RESOURCE_FAILED")

    def exception(self):
        NSInstModel.objects.filter(id=self.ns_inst_id).update(status='FAILED')
        raise NSLCMException("DELETE_NS_RESOURCE_FAILED")

    def finaldata(self):
        NSInstModel.objects.filter(id=self.ns_inst_id).update(status='null')
        pass

    @staticmethod
    def call_vnfm_to_cancel_resource(res_type, instid):
        if res_type == 'vl':
            uri = '/openoapi/nslcm/v1/ns/vls/%s' % instid
        elif res_type == 'sfc':
            uri = '/openoapi/nslcm/v1/ns/sfcs/%s' % instid
        elif res_type == 'vnf':
            uri = '/openoapi/nslcm/v1/ns/vnfs/%s' % instid
        else:
            uri = '/openoapi/nslcm/v1/ns/vnfs/%s' % instid
        req_param = {}
        ret = req_by_msb(uri, "DELETE", req_param)
        logger.info("[NS terminate] call vnfm to terminate resource[%s] result:%s" % (str(res_type), str(ret)))
        return ret

    def add_progress(self, progress, status_decs, error_code=""):
        JobUtil.add_job_status(self.job_id, progress, status_decs, error_code)

    @staticmethod
    def wait_job_mode_callback(vnfo_job_id, vnfm_job_id, job_status, jobs, progress_range, **kwargs):
        for job in jobs:
            progress = TerminateNsService.calc_progress_over_100(job['progress'], progress_range)
            if 255 == progress and '1' == kwargs['mode']:
                break
            JobUtil.add_job_status(vnfo_job_id, progress, job.get('statusdescription', ''), job.get('errorcode', ''))

        latest_progress = TerminateNsService.calc_progress_over_100(job_status['progress'], progress_range)
        if 255 == latest_progress and '1' == kwargs['mode']:
            JobUtil.add_job_status(vnfo_job_id, progress_range[1], job_status.get('statusdescription', ''),
                                   job_status.get('errorcode', ''))
        else:
            JobUtil.add_job_status(vnfo_job_id, latest_progress, job_status.get('statusdescription', ''),
                                   job_status.get('errorcode', ''))
        if job_status['status'] in ('error', 'finished'):
            return True, job_status['status']
        return False, 'processing'

    @staticmethod
    def wait_job_finish_common_call_back(vnfo_job_id, vnfm_job_id, job_status, jobs, progress_range, **kwargs):
        error_254 = False
        for job in jobs:
            progress = TerminateNsService.calc_progress_over_100(job['progress'], progress_range)
            if 254 == progress:
                logger.debug("=========254==============")
                progress = 255
                error_254 = True
            JobUtil.add_job_status(vnfo_job_id, progress, job.get('statusdescription', ""), job.get('errorcode', ""))
        latest_progress = TerminateNsService.calc_progress_over_100(job_status['progress'], progress_range)
        if 254 == latest_progress:
            logger.debug("=========254==============")
            latest_progress = 255
            error_254 = True
        JobUtil.add_job_status(vnfo_job_id, latest_progress, job_status.get('statusdescription', ""),
                               job_status.get('errorcode', ""))
        # return error_254
        if error_254:
            logger.debug("return 254")
            return True, 'error_254'
        if job_status['status'] in ('error', 'finished'):
            return True, job_status['status']
        return False, 'processing'

    @staticmethod
    def calc_progress_over_100(vnfm_progress, target_range=None):
        if target_range is None:
            target_range = [0, 100]
        progress = int(vnfm_progress)
        if progress > 100:
            return progress
        floor_progress = int(math.floor(float(target_range[1] - target_range[0]) / 100 * progress))
        target_range = floor_progress + target_range[0]
        return target_range


class DeleteNsService(object):
    def __init__(self, ns_inst_id):
        self.ns_inst_id = ns_inst_id

    def do_biz(self):
        logger.debug("[NS Delete] [do_delete] begin")

        if self.get_ns_flag() == 0:
            self.delete_ns()
            return 'true'
        else:
            return 'false'

    def get_ns_flag(self):
        nsinst = NSInstModel.objects.filter(id=self.ns_inst_id)
        if not nsinst:
            logger.error("[Ns delete] ns id not exist")
            return 255
        if not nsinst.exists():
            logger.error("[Ns delete] ns id not exist")
            return 255
        ns_status = nsinst.first().status
        if ns_status == 'null':
            return 0
        else:
            logger.error("[Ns delete] ns status not correct")
            return 255

    def delete_ns(self):
        NSInstModel.objects.filter(id=self.ns_inst_id).delete()
