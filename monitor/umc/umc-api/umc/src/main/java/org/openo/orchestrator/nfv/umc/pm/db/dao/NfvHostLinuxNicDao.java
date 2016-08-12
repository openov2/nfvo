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
package org.openo.orchestrator.nfv.umc.pm.db.dao;

import java.sql.Timestamp;
import java.util.Date;
import java.util.List;

import org.hibernate.HibernateException;
import org.hibernate.Query;
import org.hibernate.SessionFactory;
import org.openo.orchestrator.nfv.umc.db.UmcDao;
import org.openo.orchestrator.nfv.umc.pm.db.entity.NfvHostLinuxNic;
import org.openo.orchestrator.nfv.umc.pm.db.process.IPmDbQuery;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NfvHostLinuxNicDao extends UmcDao<NfvHostLinuxNic> implements IPmDbQuery {

    private static final Logger LOGGER = LoggerFactory.getLogger(NfvHostLinuxNicDao.class);

    public NfvHostLinuxNicDao(SessionFactory sessionFactory) {
        super(sessionFactory);
    }

    public List<NfvHostLinuxNic> findAll() {
        List<NfvHostLinuxNic> list = null;
        try {
            beginTransaction();
            list = list(session.createQuery("from NfvHostLinuxNic t"));
        } catch (HibernateException ex) {
            LOGGER.error("NfvHostLinuxNicDao.findAll throw exception!", ex);
        } finally {
            closeTransaction();
        }

        return list;
    }

    @SuppressWarnings("unchecked")
    @Override
    public List<NfvHostLinuxNic> queryDataFromDB(Date beginTime, Date endTime, int granularity,
            List<String> neDns) {
        List<NfvHostLinuxNic> list = null;
        try {
            String hsql =
                    "FROM NfvHostLinuxNic t WHERE t.beginTime >= :beginTime AND t.beginTime < :endTime "
                            + "AND t.granularity = :granularity AND t.nedn IN( :nednList )";

            beginTransaction();
            Query query = session.createQuery(hsql);
            query.setParameter("beginTime", new Timestamp(beginTime.getTime()));
            query.setParameter("endTime", new Timestamp(endTime.getTime()));
            query.setParameter("granularity", granularity);
            query.setParameterList("nednList", neDns);
            list = query.list();

        } catch (HibernateException ex) {
            LOGGER.error("NfvHostLinuxNicDao.queryDataFromDB throw exception!", ex);
        } finally {
            closeTransaction();
        }

        return list;
    }
}
