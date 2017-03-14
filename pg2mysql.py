#!/usr/bin/env python
import psycopg2
import sys
import getpass
import logging


def get_table_col_names(con, table_str):
    """Get the Table column names and attributes."""
    col_names = []
    try:
        cur = con.cursor()
        cur.execute("SELECT column_name, ordinal_position, is_nullable, "
                    "data_type, character_maximum_length, column_default "
                    "FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '" +
                    table_str + "' ORDER BY ordinal_position")
        for desc in cur.fetchall():
            col_names.append(desc)
        cur.close()
    except psycopg2.Error as e:
        print(e)

    return col_names


def exportCSV(con, table_str):
    """Generate a CSV of data to be inserted in MySQL using LOAD INFILE."""
    try:
        cur = con.cursor()
        io = open(("/tmp/pg2mysql_tabledata_%s.csv") % table_str, "w")
        cur.copy_to(io, table_str)
        io.close()
        cur.close()
    except psycopg2.Error as e:
        print(e)


def get_table_pkfk(con, table_str):
    """Get information about Table Constrains and Keys."""

    col_names = []
    try:
        cur = con.cursor()
        cur.execute("SELECT conname, "
                    "pg_catalog.pg_get_constraintdef(r.oid, true) as condef, "
                    "r.contype "
                    "FROM pg_catalog.pg_constraint r "
                    "WHERE r.conrelid = '" + table_str + "'::regclass "
                    "ORDER BY 1")
        for desc in cur.fetchall():
            col_names.append(desc)
        cur.close()
    except psycopg2.Error as e:
        print(e)

    return col_names


def nomax(s):
    """Helper for varchar data type writing."""
    if s is None:
        return '255'
    return str(s)


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    pg_db_name = "mydatabase"
    pg_server = "pgserver"
    pg_user = "postgres" 
    pg_passwd = getpass.getpass("Password for %s:" % pg_db_name)
    # Define our connection string
    conn_string = "host='%s' dbname='%s' user='%s' password='%s'" \
        % (pg_server, pg_db_name, pg_user, pg_passwd)

    # get a connection, if a connect cannot be made an
    # exception will be raised here
    conn = psycopg2.connect(conn_string)
    conn.set_session(readonly=True)
    conn.set_client_encoding('UTF-8')

    create_table = ""
    pk_constraints = ""
    uk_constraints = ""
    fk_constraints = ""
    load_data = ""

    psql_types = {
        "integer": "int(11)",
        "int_unsigned": "int(11) UNSIGNED",
        "smallint_unsigned": "smallint UNSIGNED",
        "bigint_unsigned": "bigint UNSIGNED",
        "serial": "int(11) auto_increment",
        "bytea": "BLOB",
        "date": "date",
        "text": "text",
        "boolean": "bool",
        "character varying": "varchar",
        "character": "char",
        "double precision": "double",
        "timestamp with time zone": "timestamp",
        "timestamp without time zone": "timestamp",
        "time with time zone": "time",
        "time without time zone": "time",
        "timestamp": "timestamp"
    }

    cursor = conn.cursor()
    cursor.execute(
        "SELECT table_name FROM information_schema.tables "
        " WHERE table_schema = 'public' and table_type = 'BASE TABLE'")
    for table in cursor.fetchall():
        exportCSV(conn, table[0])
        load_data += (
            "LOAD DATA LOCAL INFILE '/tmp/pg2mysql_tabledata_%s.csv' "
            "INTO TABLE %s;\n" % (table[0], table[0]))
        create_table += "CREATE TABLE " + table[0] + " (\n"
        logging.debug('Table: %s' % table[0])
        first = True
        pk_created = False
        for column in get_table_col_names(conn, table[0]):
            column_name = column[0]
            # ordinal_position = column[1]
            is_nullable = column[2] == 'YES'
            data_type = column[3]
            character_maximum_length = column[4]
            column_default = column[5]

            if data_type == "character" and character_maximum_length > 255:
                data_type = "character varying"

            if not first:
                create_table += ","
            else:
                create_table += " "

            create_table += "   " + column_name
            if (column_default is not None
                    and not column_default.startswith('nextval(')
                    and data_type == "text"):
                create_table += " varchar(255)"
            else:
                create_table += " " + psql_types.get(data_type, "FIXME")
            if data_type == "character varying" or data_type == "character":
                create_table += "(%s)" % nomax(character_maximum_length)

            if column_default is not None:
                if column_default.startswith('nextval('):
                    create_table += " auto_increment primary key"
                    pk_created = True
                elif column_default.startswith("('now'::text)::date"):
                    pass
                else:
                    idx = column_default.find("::")
                    if idx == -1:
                        idx = len(column_default)
                    create_table += " DEFAULT " + column_default[:idx]
            if not is_nullable:
                create_table += " NOT NULL"

            vars = (table[0], column_name, character_maximum_length,
                    column_default, data_type, is_nullable)
            logging.debug("%s.%s: %s - %s - %s - %s" % vars)

            create_table += "\n"
            first = False
        create_table += ") ENGINE=innodb;\n\n"

        for column in get_table_pkfk(conn, table[0]):
            constraint_name = column[0]
            constraint_def = column[1]
            constraint_type = column[2]

            constraint = ""
            constraint += "ALTER TABLE " + table[0] + "\n"
            constraint += "ADD CONSTRAINT " + constraint_name + "\n"
            constraint += constraint_def + ";\n"

            if constraint_type == 'p':
                if not pk_created:
                    pk_constraints += constraint + "\n"
            elif constraint_type == 'u':
                uk_constraints += constraint + "\n"
            else:
                fk_constraints += constraint + "\n"

    conn.close()

    print(create_table)
    print(pk_constraints)
    print(load_data)
    print(uk_constraints)
    print(fk_constraints)

if __name__ == "__main__":
    main()
