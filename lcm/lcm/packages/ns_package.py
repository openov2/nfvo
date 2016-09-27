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

import json
import logging
import uuid
import traceback
import sys

from lcm.pub.database.models import NSDModel, NSInstModel, NfPackageModel
from lcm.pub.utils.values import ignore_case_get
from lcm.pub.msapi.catalog import STATUS_ONBOARDED, P_STATUS_DELETEFAILED
from lcm.pub.msapi.catalog import query_csar_from_catalog, set_csar_state
from lcm.pub.msapi.catalog import query_rawdata_from_catalog, delete_csar_from_catalog
from lcm.pub.exceptions import NSLCMException

logger = logging.getLogger(__name__)

STATUS_SUCCESS, STATUS_FAILED = "success", "failed"


def fmt_ns_pkg_rsp(status, desc, error_code="500"):
    return [0, {"status": status, "statusDescription": desc, "errorCode": error_code}]


def ns_common_call(fun, csar_id):
    ret = None
    try:
        ret = fun(csar_id)
        if ret[0] != 0:
            return fmt_ns_pkg_rsp(STATUS_FAILED, ret[1])
    except NSLCMException as e:
        return fmt_ns_pkg_rsp(STATUS_FAILED, e.message)
    except:
        logger.error(traceback.format_exc())
        return fmt_ns_pkg_rsp(STATUS_FAILED, str(sys.exc_info()))
    return fmt_ns_pkg_rsp(STATUS_SUCCESS, ret[1], "")


def ns_on_boarding(csar_id):
    return ns_common_call(NsPackage().on_boarding, csar_id)


def ns_delete_csar(csar_id):
    return ns_common_call(NsPackage().delete_csar, csar_id)


def ns_delete_pending_csar(csar_id):
    return ns_common_call(NsPackage().delete_pending_csar, csar_id)


def ns_get_csar(csar_id):
    ret = None
    try:
        ret = NsPackage().get_csar(csar_id)
    except NSLCMException as e:
        return [1, e.message]
    except:
        logger.error(traceback.format_exc())
        return [1, str(sys.exc_info())]
    return ret


###############################################################################################################


class NsPackage(object):
    """
    Actions for ns package.
    """

    def __init__(self):
        pass

    def on_boarding(self, csar_id):
        csar = query_csar_from_catalog(csar_id)
        if ignore_case_get(csar, "onBoardState") == STATUS_ONBOARDED:
            raise NSLCMException("CSAR(%s) already onBoarded." % csar_id)

        nsd = query_rawdata_from_catalog(csar_id)  # TODO: convert to inner model
        nsd_id = nsd["rawData"]["metadata"]["id"]
        if NSDModel.objects.filter(nsd_id=nsd_id):
            raise NSLCMException("NSD(%s) already exists." % nsd_id)

        for vnf in nsd["vnfs"]:
            vnfd_id = vnf["properties"]["id"]
            if not NfPackageModel.objects.filter(nfpackageid=vnfd_id):
                raise NSLCMException("VNF package(%s) is not onBoarded." % vnfd_id)
            if query_csar_from_catalog(vnfd_id, "onBoardState") != STATUS_ONBOARDED:
                raise NSLCMException("VNF package(%s) is not onBoarded on catalog." % vnfd_id)

        NSDModel(
            id=csar_id,
            nsd_id=nsd_id,
            name=nsd["rawData"]["metadata"]["name"],
            vendor=nsd["rawData"]["metadata"]["vendor"],
            description=nsd["rawData"]["metadata"]["description"],
            version=nsd["rawData"]["metadata"]["version"],
            nsd_model=json.JSONEncoder().encode(nsd)).save()

        set_csar_state(csar_id, "onBoardState", STATUS_ONBOARDED)

        return [0, "CSAR(%s) onBoarded successfully." % csar_id]

    def delete_csar(self, csar_id):
        if not NSDModel.objects.filter(id=csar_id):
            return delete_csar_from_catalog(csar_id)

        if NSInstModel.objects.filter(nspackage_id=csar_id):
            return set_csar_state(csar_id, "deletionPending", True)

        ret = delete_csar_from_catalog(csar_id)
        if ret[0] == 0:
            NSDModel.objects.filter(id=csar_id).delete()
        return ret

    def delete_pending_csar(self, csar_id):
        if not NSDModel.objects.filter(id=csar_id):
            return [0, "Delete pending CSAR(%s) successfully." % csar_id]

        pending = query_csar_from_catalog(csar_id, "deletionPending")

        if pending.lower() == "false":
            return [1, "CSAR(%s) need not to be deleted." % csar_id]

        if NSInstModel.objects.filter(nspackage_id=csar_id):
            return [1, "CSAR(%s) is in using, cannot be deleted." % csar_id]

        ret = delete_csar_from_catalog(csar_id)
        if ret[0] == 0:
            NSDModel.objects.filter(id=csar_id).delete()
        return ret

    def get_csar(self, csar_id):
        package_info = {}

        csar_in_catalog = query_csar_from_catalog(csar_id)
        props_of_catalog = [
            "name", "provider", "version", "operationalState", "usageState",
            "onBoardState", "processState", "deletionPending", "downloadUri",
            "createTime", "modifyTime", "format", "size"]
        for prop in props_of_catalog:
            package_info[prop] = ignore_case_get(csar_in_catalog, prop)

        csars = NSDModel.objects.filter(id=csar_id)
        if csars:
            package_info["nsdId"] = csars[0].nsd_id
            package_info["nsdProvider"] = csars[0].vendor
            package_info["nsdVersion"] = csars[0].version

        nss = NSInstModel.objects.filter(nspackage_id=csar_id)
        ns_instance_info = [{"nsInstanceId": ns.id, "nsInstanceName": ns.name} for ns in nss]

        return [0, {"csarId": csar_id, "packageInfo": package_info, "nsInstanceInfo": ns_instance_info}]
