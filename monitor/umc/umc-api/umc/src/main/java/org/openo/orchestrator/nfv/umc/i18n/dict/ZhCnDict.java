/**
 * Copyright (C) 2015 CMCC, Inc. and others. All rights reserved. (CMCC)
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */
package org.openo.orchestrator.nfv.umc.i18n.dict;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.openo.orchestrator.nfv.umc.i18n.I18n;
import org.openo.orchestrator.nfv.umc.i18n.I18nOpr;
import org.openo.orchestrator.nfv.umc.i18n.common.I18nCacheBuilder;

/**
 * @author wangjiangping
 * @date 2016/4/20 11:07:32
 * @description zh-cn dict.
 */
public class ZhCnDict extends I18n implements I18nOpr {

    private static ZhCnDict zhCnDict = null;
    Map<String, String> dict = new HashMap<String, String>();

    public ZhCnDict(Map<String, String> cacheMap) {
        dict.putAll(cacheMap);
    }

    public static ZhCnDict getInstance(List<Map<String, String>> dictCache) {
        if (zhCnDict == null) {
            zhCnDict = new ZhCnDict(dictCache.get(I18nCacheBuilder.I18N_ZH_CN_INDEX));
        }

        return zhCnDict;
    }

    /*
     * (non-Javadoc)
     *
     * @see org.openo.orchestrator.nfv.umc.i18n.I18nOpr#translate(java.lang.String)
     */
    @Override
    public String translate(String key) {
        String value = zhCnDict.dict.get(key);
        if (value != null) {
            return value;
        }
        return key;
    }

    /*
     * (non-Javadoc)
     *
     * @see org.openo.orchestrator.nfv.umc.i18n.I18nOpr#translate(java.lang.String, java.util.Map)
     */
    @Override
    public String translate(String key, Map<String, String> vars) {
        String value = translate(key);

        if (value.equals(key) || vars == null) {
            return key;
        }

        for (String var : vars.keySet()) {
            value = value.replaceAll("\\$\\{" + var + "\\}", vars.get(var));
        }
        return value;
    }

}
