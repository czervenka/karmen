import psycopg2
from psycopg2 import sql
import psycopg2.extras
from server.database import get_connection


def add_printer(**kwargs):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO printers (uuid, name, hostname, ip, port, client, site_id, client_props, printer_props, protocol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                kwargs["uuid"],
                kwargs["name"],
                kwargs["hostname"],
                kwargs["ip"],
                kwargs.get("port"),
                kwargs["client"],
		kwargs["site_id"],
                psycopg2.extras.Json(kwargs["client_props"]),
                psycopg2.extras.Json(kwargs.get("printer_props", None)),
                kwargs.get("protocol", "http"),
            ),
        )
        cursor.close()


def update_printer(**kwargs):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE printers SET name = %s, hostname = %s, ip = %s, port = %s, client = %s, site_id = %s, client_props = %s, printer_props = %s, protocol = %s where uuid = %s",
            (
                kwargs["name"],
                kwargs["hostname"],
                kwargs["ip"],
                kwargs.get("port"),
                kwargs["client"],
		kwargs["site_id"],
                psycopg2.extras.Json(kwargs["client_props"]),
                psycopg2.extras.Json(kwargs["printer_props"]),
                kwargs["protocol"],
                kwargs["uuid"],
            ),
        )
        cursor.close()


def get_printers(site_id):
    with get_connection() as connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT uuid, name, hostname, ip, port, client, client_props, printer_props, protocol FROM printers WHERE site_id=%s",
	    (site_id,),
        )
        data = cursor.fetchall()
        cursor.close()
        return data


def get_printer(uuid):
    with get_connection() as connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT uuid, name, hostname, ip, port, client, client_props, printer_props, protocol FROM printers where uuid = %s",
            (uuid,),
        )
        data = cursor.fetchone()
        cursor.close()
        return data


def get_printer_by_network_props(site_id, hostname, host, port):
    def _is_or_equal(column, value):
        if value is None:
            return sql.SQL("{} is null").format(sql.Identifier(column))
        else:
            return sql.SQL("{} = {}").format(sql.Identifier(column), sql.Literal(value))

    with get_connection() as connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        basequery = sql.SQL(
            "SELECT uuid, name, hostname, ip, port, client, client_props, printer_props, protocol FROM printers where"
        )
        query = sql.SQL(" ").join(
            [
                basequery,
                sql.SQL(" and ").join(
                    [
                        sql.SQL("site_id = {}").format(sql.Literal(site_id)),
                        _is_or_equal("hostname", hostname),
                        _is_or_equal("ip", ip),
                        _is_or_equal("port", port),
                    ]
                ),
            ]
        )
        cursor.execute(query)
        data = cursor.fetchone()
        cursor.close()
        return data


def delete_printer(uuid):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM printers where uuid = %s", (uuid,))
        cursor.close()
