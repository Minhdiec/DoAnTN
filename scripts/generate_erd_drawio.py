from __future__ import annotations

import html
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = ROOT / "astraea_eyewear_db.sql"
OUT_PATH = ROOT / "Astraea_ERD_from_DB.drawio"

TABLES = [
    "accounts_user",
    "products_category",
    "products_product",
    "products_productimage",
    "cart_cart",
    "cart_cartitem",
    "favorites_favorite",
    "favorites_favorite_products",
    "orders_order",
    "orders_orderitem",
    "reviews_review",
    "reviews_reviewmedia",
    "tryon_glassesoverlay",
    "wallet_wallet",
    "wallet_transaction",
]

DISPLAY = {
    "accounts_user": "User",
    "products_category": "Category",
    "products_product": "Product",
    "products_productimage": "ProductImage",
    "cart_cart": "Cart",
    "cart_cartitem": "CartItem",
    "favorites_favorite": "Favorite",
    "favorites_favorite_products": "Favorite_Product",
    "orders_order": "Order",
    "orders_orderitem": "OrderItem",
    "reviews_review": "Review",
    "reviews_reviewmedia": "ReviewMedia",
    "tryon_glassesoverlay": "GlassesOverlay",
    "wallet_wallet": "Wallet",
    "wallet_transaction": "Transaction",
}

POSITIONS = {
    "accounts_user": (40, 60),
    "products_category": (40, 380),
    "products_product": (360, 280),
    "products_productimage": (700, 40),
    "tryon_glassesoverlay": (700, 230),
    "cart_cart": (360, 40),
    "cart_cartitem": (700, 420),
    "favorites_favorite": (360, 560),
    "favorites_favorite_products": (700, 610),
    "orders_order": (1040, 80),
    "orders_orderitem": (1040, 320),
    "reviews_review": (1380, 260),
    "reviews_reviewmedia": (1720, 310),
    "wallet_wallet": (1040, 610),
    "wallet_transaction": (1380, 610),
}

TABLE_W = 270
ROW_H = 22


def parse_sql(sql: str):
    tables: dict[str, list[tuple[str, str]]] = {}
    uniques: dict[str, set[str]] = {table: set() for table in TABLES}
    fks: list[tuple[str, str, str, str, str]] = []

    for table, body in re.findall(
        r"CREATE TABLE `([^`]+)` \((.*?)\) ENGINE=", sql, flags=re.S
    ):
        if table not in TABLES:
            continue
        columns: list[tuple[str, str]] = []
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line.startswith("`"):
                continue
            m = re.match(r"`([^`]+)`\s+(.+)", line)
            if not m:
                continue
            name = m.group(1)
            dtype = m.group(2).split(" COMMENT ")[0]
            columns.append((name, dtype))
        tables[table] = columns

    for table in TABLES:
        for pattern in [
            rf"ALTER TABLE `{re.escape(table)}`(.*?);",
        ]:
            for block in re.findall(pattern, sql, flags=re.S):
                for cols in re.findall(r"ADD UNIQUE KEY `[^`]+` \(`([^`]+)`\)", block):
                    uniques[table].add(cols)
                for name, src_col, dst_table, dst_col in re.findall(
                    r"ADD CONSTRAINT `([^`]+)` FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\)",
                    block,
                ):
                    if dst_table in TABLES:
                        fks.append((table, src_col, dst_table, dst_col, name))

    return tables, uniques, fks


def table_label(table: str, columns: list[tuple[str, str]], unique_cols: set[str]) -> str:
    lines = [
        f"<b>{html.escape(DISPLAY[table])}</b>",
        f"<font color='#5f6b7a'>{html.escape(table)}</font>",
        "<hr size='1'>",
    ]
    for name, dtype in columns:
        key = "PK" if name == "id" else "UQ" if name in unique_cols else ""
        if name.endswith("_id"):
            key = "FK" if not key else f"{key}, FK"
        short_type = dtype.split()[0].upper()
        lines.append(
            f"<font face='Consolas'>{html.escape(name)}</font>"
            f" <font color='#6b7280'>{html.escape(short_type)}</font>"
            f"{' <font color=\"#b45309\">[' + key + ']</font>' if key else ''}"
        )
    return "<br>".join(lines)


def add_cell(root, cell_id, value="", style="", parent="1", vertex=None, edge=None):
    attrs = {"id": cell_id, "value": value, "style": style, "parent": parent}
    if vertex is not None:
        attrs["vertex"] = "1"
    if edge is not None:
        attrs["edge"] = "1"
        attrs["source"] = edge[0]
        attrs["target"] = edge[1]
    cell = ET.SubElement(root, "mxCell", attrs)
    return cell


def main() -> None:
    sql = SQL_PATH.read_text(encoding="utf-8", errors="ignore")
    tables, uniques, fks = parse_sql(sql)

    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-09-22T00:00:00.000Z",
            "agent": "Codex",
            "version": "27.0.0",
            "type": "device",
        },
    )
    diagram = ET.SubElement(mxfile, "diagram", {"id": str(uuid.uuid4()), "name": "Astraea ERD"})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "2000",
            "dy": "1200",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "2200",
            "pageHeight": "1000",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    table_ids = {table: f"tbl_{table}" for table in TABLES}
    for table in TABLES:
        x, y = POSITIONS[table]
        height = 58 + len(tables.get(table, [])) * ROW_H
        style = (
            "rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
            "spacing=8;fontSize=11;fontColor=#111827;strokeColor=#1f2937;"
            "fillColor=#f8fafc;shadow=0;"
        )
        cell = add_cell(
            root,
            table_ids[table],
            table_label(table, tables.get(table, []), uniques[table]),
            style,
            vertex=True,
        )
        ET.SubElement(
            cell,
            "mxGeometry",
            {"x": str(x), "y": str(y), "width": str(TABLE_W), "height": str(height), "as": "geometry"},
        )

    edge_style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
        "html=1;strokeWidth=2;strokeColor=#374151;endArrow=block;endFill=1;"
        "fontSize=11;fontColor=#111827;labelBackgroundColor=#ffffff;"
    )
    for idx, (src, src_col, dst, dst_col, _) in enumerate(fks, 1):
        cardinality = "1:1" if src_col in uniques[src] else "N:1"
        label = f"{cardinality}  {src_col} -> {dst_col}"
        cell = add_cell(
            root,
            f"edge_{idx}",
            html.escape(label),
            edge_style,
            edge=(table_ids[src], table_ids[dst]),
        )
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    ET.indent(mxfile, space="  ")
    OUT_PATH.write_text(
        ET.tostring(mxfile, encoding="unicode", method="xml"),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH} with {len(TABLES)} tables and {len(fks)} relationships")


if __name__ == "__main__":
    main()
