# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from fastapi import HTTPException, Request, status

from airflow.api_fastapi.common.db.common import SessionDep
from airflow.api_fastapi.common.router import AirflowRouter
from airflow.api_fastapi.core_api.datamodels.ui.structure import StructureDataResponse
from airflow.api_fastapi.core_api.openapi.exceptions import create_openapi_http_exception_doc
from airflow.utils.dag_edges import dag_edges
from airflow.utils.task_group import task_group_to_dict

structure_router = AirflowRouter(tags=["Structure"], prefix="/structure")


@structure_router.get(
    "/structure_data",
    include_in_schema=False,
    responses=create_openapi_http_exception_doc([status.HTTP_404_NOT_FOUND]),
)
def structure_data(
    session: SessionDep,
    dag_id: str,
    request: Request,
    root: str | None = None,
    include_upstream: bool = False,
    include_downstream: bool = False,
) -> StructureDataResponse:
    """Get Structure Data."""
    dag = request.app.state.dag_bag.get_dag(dag_id)

    if dag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Dag with id {dag_id} was not found")

    if root:
        dag = dag.partial_subset(
            task_ids_or_regex=root, include_upstream=include_upstream, include_downstream=include_downstream
        )

    nodes = [
        task_group_to_dict(child) for child in sorted(dag.task_group.children.values(), key=lambda t: t.label)
    ]
    edges = dag_edges(dag)

    data = {
        "arrange": dag.orientation,
        "nodes": nodes,
        "edges": edges,
    }

    return StructureDataResponse(**data)
