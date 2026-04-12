from __future__ import annotations

import uuid
from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.db import get_session
from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.membership import DirectMembership
from app.models.user import DirectoryUser

router = APIRouter(
    prefix="/api/directories/{directory_id}",
    tags=["graph"],
)


class NodeData(BaseModel):
    sam_account_name: str | None = None
    mail: str | None = None
    disabled: bool | None = None
    member_count: int | None = None
    description: str | None = None


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    data: NodeData


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "member"


class GraphMeta(BaseModel):
    node_count: int
    edge_count: int
    truncated: bool


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    meta: GraphMeta


def _get_directory_or_404(directory_id: uuid.UUID, session: Session) -> Directory:
    directory = session.get(Directory, directory_id)
    if directory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")
    return directory


@router.get("/graph", response_model=GraphResponse)
def get_graph(
    directory_id: uuid.UUID,
    root_dn: str | None = Query(default=None),
    depth: int = Query(default=2, ge=1, le=5),
    node_limit: int = Query(default=500, ge=1, le=5000),
    session: Session = Depends(get_session),
) -> GraphResponse:
    """Return a subgraph of the directory's membership structure for React Flow."""
    _get_directory_or_404(directory_id, session)

    if root_dn:
        return _bfs_from_root(session, directory_id, root_dn, depth, node_limit)
    return _top_groups_view(session, directory_id, node_limit)


def _bfs_from_root(
    session: Session,
    directory_id: uuid.UUID,
    root_dn: str,
    max_depth: int,
    node_limit: int,
) -> GraphResponse:
    """BFS from root_dn in both directions up to max_depth hops."""
    visited_dns: set[str] = {root_dn}
    edge_set: set[tuple[str, str]] = set()
    queue: deque[tuple[str, int]] = deque([(root_dn, 0)])

    all_memberships = session.exec(
        select(DirectMembership).where(DirectMembership.directory_id == directory_id)
    ).all()

    children_of: dict[str, list[DirectMembership]] = {}
    parents_of: dict[str, list[DirectMembership]] = {}
    for m in all_memberships:
        children_of.setdefault(m.parent_dn, []).append(m)
        parents_of.setdefault(m.child_dn, []).append(m)

    while queue and len(visited_dns) < node_limit:
        current_dn, current_depth = queue.popleft()
        if current_depth >= max_depth:
            continue

        for m in children_of.get(current_dn, []):
            edge_set.add((m.parent_dn, m.child_dn))
            if m.child_dn not in visited_dns:
                visited_dns.add(m.child_dn)
                queue.append((m.child_dn, current_depth + 1))
                if len(visited_dns) >= node_limit:
                    break

        if len(visited_dns) >= node_limit:
            break

        for m in parents_of.get(current_dn, []):
            edge_set.add((m.parent_dn, m.child_dn))
            if m.parent_dn not in visited_dns:
                visited_dns.add(m.parent_dn)
                queue.append((m.parent_dn, current_depth + 1))
                if len(visited_dns) >= node_limit:
                    break

    truncated = len(visited_dns) >= node_limit
    return _build_response(session, directory_id, visited_dns, edge_set, truncated)


def _top_groups_view(
    session: Session,
    directory_id: uuid.UUID,
    node_limit: int,
) -> GraphResponse:
    """Default view: top groups by direct member count + their immediate members."""
    from sqlalchemy import func

    top_groups = session.exec(
        select(DirectMembership.parent_dn, func.count().label("cnt"))
        .where(DirectMembership.directory_id == directory_id)
        .group_by(DirectMembership.parent_dn)
        .order_by(func.count().desc())
        .limit(10)
    ).all()

    visited_dns: set[str] = set()
    edge_set: set[tuple[str, str]] = set()

    for group_dn, _cnt in top_groups:
        visited_dns.add(group_dn)

    for group_dn, _cnt in top_groups:
        if len(visited_dns) >= node_limit:
            break
        members = session.exec(
            select(DirectMembership)
            .where(
                DirectMembership.directory_id == directory_id,
                DirectMembership.parent_dn == group_dn,
            )
        ).all()
        for m in members:
            edge_set.add((m.parent_dn, m.child_dn))
            visited_dns.add(m.child_dn)
            if len(visited_dns) >= node_limit:
                break

        parent_edges = session.exec(
            select(DirectMembership)
            .where(
                DirectMembership.directory_id == directory_id,
                DirectMembership.child_dn == group_dn,
            )
        ).all()
        for m in parent_edges:
            edge_set.add((m.parent_dn, m.child_dn))
            visited_dns.add(m.parent_dn)
            if len(visited_dns) >= node_limit:
                break

    truncated = len(visited_dns) >= node_limit
    return _build_response(session, directory_id, visited_dns, edge_set, truncated)


def _build_response(
    session: Session,
    directory_id: uuid.UUID,
    dns: set[str],
    edge_set: set[tuple[str, str]],
    truncated: bool,
) -> GraphResponse:
    """Resolve DNs to nodes and build the final response."""
    users_by_dn: dict[str, DirectoryUser] = {}
    groups_by_dn: dict[str, DirectoryGroup] = {}

    if dns:
        dn_list = list(dns)
        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == directory_id,
                col(DirectoryUser.dn).in_(dn_list),
            )
        ).all()
        for u in users:
            users_by_dn[u.dn] = u

        groups = session.exec(
            select(DirectoryGroup).where(
                DirectoryGroup.directory_id == directory_id,
                col(DirectoryGroup.dn).in_(dn_list),
            )
        ).all()
        for g in groups:
            groups_by_dn[g.dn] = g

    nodes: list[GraphNode] = []
    for dn in dns:
        if dn in users_by_dn:
            u = users_by_dn[dn]
            nodes.append(GraphNode(
                id=dn,
                type="user",
                label=u.display_name,
                data=NodeData(
                    sam_account_name=u.sam_account_name,
                    mail=u.mail,
                    disabled=u.account_disabled,
                ),
            ))
        elif dn in groups_by_dn:
            g = groups_by_dn[dn]
            nodes.append(GraphNode(
                id=dn,
                type="group",
                label=g.name,
                data=NodeData(
                    description=g.description,
                ),
            ))

    edges = [
        GraphEdge(id=f"{src}->{tgt}", source=src, target=tgt)
        for src, tgt in edge_set
    ]

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        meta=GraphMeta(
            node_count=len(nodes),
            edge_count=len(edges),
            truncated=truncated,
        ),
    )
