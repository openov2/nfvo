/*
 * Copyright 2017 Huawei Technologies Co., Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.openo.nfvo.vnfmadapter.service.adapter.impl;

import static org.junit.Assert.assertTrue;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import org.junit.Before;
import org.junit.Test;
import org.openo.baseservice.roa.util.restclient.RestfulResponse;
import org.openo.nfvo.vnfmadapter.common.servicetoken.VNFRestfulUtil;
import org.openo.nfvo.vnfmadapter.testutils.JsonUtil;

import mockit.Mock;
import mockit.MockUp;
import net.sf.json.JSONObject;

/**
 * <br>
 * <p>
 * </p>
 * 
 * @author
 * @version NFVO 0.5 Jan 24, 2017
 */
public class Driver2MSBManagerTest {

    Driver2MSBManager manager = new Driver2MSBManager();

    Map<String, String> vim = new HashMap<String, String>();

    @Before
    public void setUp() {
        vim.put("vimId", "123");
        vim.put("name", "123");
        vim.put("url", "123");
        vim.put("userName", "123");
        vim.put("password", "123");
        vim.put("type", "123");
        vim.put("version", "123");
    }

    @Test
    public void registerDriverTestNullResp() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();

                return null;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.registerDriver(paramsMap, new JSONObject());
        assertTrue(obj.get("reason").equals("RestfulResponse is null."));
    }

    @Test
    public void registerDriverCreateSuccess() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(201);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.registerDriver(paramsMap, new JSONObject());
        assertTrue(Integer.valueOf(obj.get("retCode").toString()) == 201);
    }

    @Test
    public void registerDriverOkSuccess() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(200);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.registerDriver(paramsMap, new JSONObject());
        assertTrue(Integer.valueOf(obj.get("retCode").toString()) == -1);
    }

    @Test
    public void registerDriverTestInvalidParams() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(415);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.registerDriver(paramsMap, new JSONObject());
        assertTrue(obj.get("reason").equals("MSB return fail,invalid parameters."));
    }

    @Test
    public void registerDriverTestInternalError() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(500);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.registerDriver(paramsMap, new JSONObject());
        assertTrue(obj.get("reason").equals("MSB return fail,internal system error."));
    }

    @Test
    public void unregisterDriverTestNullResp() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();

                return null;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.unregisterDriver(paramsMap);
        assertTrue(obj.get("reason").equals("RestfulResponse is null."));
    }

    @Test
    public void unregisterDriverDeleteSuccess() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(204);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.unregisterDriver(paramsMap);
        assertTrue(Integer.valueOf(obj.get("retCode").toString()) == 204);
    }

    @Test
    public void unregisterDriverResourceNotFound() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(404);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.unregisterDriver(paramsMap);
        assertTrue(obj.get("reason").equals("MSB return fail,can't find the service instance."));
    }

    @Test
    public void unregisterDriverTestInvalidParams() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(415);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.unregisterDriver(paramsMap);
        assertTrue(obj.get("reason").equals("MSB return fail,invalid parameters."));
    }

    @Test
    public void unregisterDriverTestInternalError() {
        new MockUp<VNFRestfulUtil>() {

            @Mock
            public RestfulResponse getRemoteResponse(Map<String, String> paramsMap, String params) {
                RestfulResponse response = new RestfulResponse();
                response.setStatus(500);

                String vimStr = toJson(vim);
                response.setResponseJson(vimStr);
                return response;
            }
        };
        Map<String, String> paramsMap = new HashMap<>();
        paramsMap.put("url", "/test/openoapi");
        paramsMap.put("path", "http://localhost:8080");
        paramsMap.put("methodType", "get");
        JSONObject obj = manager.unregisterDriver(paramsMap);
        assertTrue(obj.get("reason").equals("MSB return fail,internal system error."));
    }

    public static String toJson(Map o) {
        try {
            return JsonUtil.marshal(o);
        } catch(IOException e) {
            return "";
        }
    }
}
