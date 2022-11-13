import PySimpleGUI as SG
import mysql.connector

where_operators = ['=', '!=', '>=', '<=', 'like', 'is', 'is not', 'between', 'in', 'not in']
query_log = []


def get_all_tables(cursor, schema):
    query = 'SELECT table_name FROM information_schema.tables WHERE table_schema = %s;'
    query_log.append(query)
    cursor.execute(query, (schema, ))
    result = cursor.fetchall()
    return [item[0] for item in result]


def get_table_headers(cursor, schema, table_name):
    query = 'SELECT COLUMN_NAME from INFORMATION_SCHEMA.COLUMNS where ' \
            'table_schema = %s and table_name = %s'
    query_log.append(query)
    cursor.execute(query, (schema, table_name))
    result = cursor.fetchall()
    return [item[0] for item in result]


def get_table_data(cursor, table_name, table_headers, where_clause="", order_clause="", limit_clause=""):
    query = f'SELECT {",".join(table_headers)} FROM {table_name}'+where_clause+order_clause+limit_clause
    query_log.append(query)
    cursor.execute(query)
    result = cursor.fetchall()
    result_itemlist = []
    for item in result:
        result_itemlist.append(list(item))
    count_query = f'SELECT count(*) FROM {table_name}'
    query_log.append(count_query)
    cursor.execute(count_query)
    count = cursor.fetchall()[0][0]
    return result_itemlist, count


def show_query_log():
    query_layout = [
        [SG.Multiline('\n'.join(query_log), size=(200, 30))],
    ]
    window = SG.Window('История запросов', query_layout)

    while True:
        event, values = window.read()

        if event == SG.WIN_CLOSED or event == 'Cancel':
            break

    window.close()


def initialize_main_window(cursor, settings, current_table, all_tables,
                           where_clause, order_clause, limit_clause, num_rows=10):
    table_header = get_table_headers(cursor, settings['database'], current_table)
    table_data, table_count = get_table_data(cursor, current_table,
                                                    table_header, where_clause, order_clause, limit_clause)
    table = [[SG.Table(values=table_data, headings=table_header, max_col_width=10,
                       auto_size_columns=True,
                       justification='center',
                       num_rows=num_rows,
                       key='table',
                       row_height=35)]]

    top_text_layout = [SG.Text('Table                  '),
                       SG.VerticalSeparator(),
                       SG.Text('Num Rows To Display'),
                       SG.VerticalSeparator(),
                       SG.Text('Order By', pad=((0, 0), (0, 0))),
                       SG.Combo(['ASC', 'DESC'], default_value='ASC', pad=((0, 0), (0, 0)), key='asc_desc'),
                       SG.Checkbox('Enable', key='order_enable'),
                       SG.VerticalSeparator(),
                       SG.Text('Limit', pad=((0, 0), (0, 0))), SG.Checkbox('Enable', key='limit_enable'),
                       SG.VerticalSeparator(),
                       SG.Text('Where', pad=((0, 0), (0, 0))), SG.Checkbox('Enable', key='where_enable'),
                       SG.Button('Apply Filters', pad=((170, 0), (0, 0)), key='apply_filters')]

    top_input_layout = [SG.Combo(all_tables, default_value=current_table, enable_events=True, key='table_choose'),
                        SG.VerticalSeparator(),
                        SG.Spin([i for i in range(1, 21)], initial_value=num_rows, size=(15, 1), key='numrows_change',
                                enable_events=True),
                        SG.VerticalSeparator(pad=((17, 0), (0, 0))),
                        SG.Combo(table_header, default_value='None', key='order_change', size=(20, 1)),
                        SG.VerticalSeparator(pad=((28, 0), (0, 0))),
                        SG.Input(key='l_limit', default_text='0', size=(5, 5)),
                        SG.Input(key='r_limit', default_text='100', size=(5, 5)),
                        SG.VerticalSeparator(pad=((21, 0), (0, 0))),
                        SG.Combo(table_header, default_value=table_header[0],
                                 size=(15, 1), pad=(5, 0), key='where_column'),
                        SG.Combo(where_operators, default_value=where_operators[0], size=(10, 1), key='where_operator'),
                        SG.Input(key='where_value', default_text="'qwerty123'", size=(20, 1))]

    bottom_layout = [[SG.Input(size=(18, 1), pad=(0, 0), readonly=True,
                               default_text=item, text_color='black') for item in table_header],
                     [SG.Input(size=(18, 1), pad=(0, 0), key=f'input_{i}') for i in range(len(table_header))],
                     [SG.Button('UPDATE', pad=((0, 5), (5, 5)), size=(10, 0)),
                      SG.Combo(table_header, default_value=table_header[0], pad=((0, 5), (5, 5)),
                               key='update_key'),
                      SG.Combo(where_operators, default_value=where_operators[0], pad=((0, 5), (5, 5)),
                               key='update_op'),
                      SG.Input(key='update_keyvalue', pad=((0, 5), (5, 5)), size=(30, 0))],
                     [SG.Button('DELETE', pad=((0, 5), (5, 5)), size=(10, 0)),
                      SG.Combo(table_header, default_value=table_header[0], pad=((0, 5), (5, 5)), key='delete_key'),
                      SG.Combo(where_operators, default_value=where_operators[0], pad=((0, 5), (5, 5)),
                               key='delete_op'),
                      SG.Input(key='delete_keyvalue', pad=((0, 5), (5, 5)), size=(30, 0))]]

    layout = [top_text_layout,
              top_input_layout,
              [SG.Text('Table row count: '+str(table_count)), SG.Button('Query Log', key='query_log')],
              table,
              [SG.HorizontalSeparator()],
              [SG.Button('INSERT', pad=((0, 0), (5, 5)), size=(10, 0))]]
    layout.extend(bottom_layout)

    window = SG.Window('Курсовая работа (Python GUI + MySQL)', layout)
    return window


def insert_into_table(cursor, db, current_table, headers, values):
    values_placeholder = ", ".join(['%s' for _ in range(len(headers))])
    query = f'INSERT INTO {current_table} ({", ".join(headers)}) VALUES ({values_placeholder})'
    query_log.append(query)
    cursor.execute(query, values)
    db.commit()


def update_table(cursor, db, current_table, headers, values, update_key, update_key_value, update_op):
    update_param_str = ''
    for header, value in zip(headers, values):
        if value == 'NULL':
            update_param_str += f"{header} = {value}, "
        else:
            update_param_str += f"{header} = '{value}', "

    query = f"UPDATE {current_table} SET {update_param_str[:-2]} WHERE {update_key} {update_op} '{update_key_value}'"
    query_log.append(query)
    cursor.execute(query)
    db.commit()


def delete_from_table(cursor, db, current_table, delete_key, delete_key_value, delete_op):
    query = f'DELETE FROM {current_table} WHERE {delete_key} {delete_op} {delete_key_value}'
    query_log.append(query)
    cursor.execute(query)
    db.commit()


def gui(db, cursor, logger, settings):
    SG.theme('Dark')
    all_tables = get_all_tables(cursor, settings['database'])
    current_table = all_tables[0]
    num_rows = 10
    order_clause, limit_clause, where_clause = ('', '', '')
    window = initialize_main_window(cursor, settings, current_table, all_tables,
                                    where_clause, order_clause, limit_clause, num_rows=num_rows)
    while True:
        event, values = window.read()

        if event == SG.WIN_CLOSED or event == 'Cancel':
            break

        if event == 'table_choose':

            current_table = values['table_choose']
            new_window = initialize_main_window(cursor, settings, current_table, all_tables,
                                                where_clause, order_clause, limit_clause, num_rows=num_rows)
            window.close()
            window = new_window
        if event == 'numrows_change':

            current_table = values['table_choose']
            num_rows = values['numrows_change']
            new_window = initialize_main_window(cursor, settings, current_table, all_tables,
                                                where_clause, order_clause, limit_clause, num_rows=num_rows)
            window.close()
            window = new_window
        if event == 'INSERT':

            table_headers = get_table_headers(cursor, settings['database'], current_table)
            insert_list = []
            for i in range(len(table_headers)):
                temp = values[f'input_{i}']
                if temp == '':
                    temp = None
                insert_list.append(temp)
            try:
                insert_into_table(cursor, db, current_table, table_headers, insert_list)
            except mysql.connector.errors.Error as e:
                SG.Popup(e)
            else:
                new_window = initialize_main_window(cursor, settings, current_table, all_tables,
                                                    where_clause, order_clause, limit_clause, num_rows=num_rows)
                window.close()
                window = new_window

        if event == 'UPDATE':
            table_headers = get_table_headers(cursor, settings['database'], current_table)
            update_list = []
            for i in range(len(table_headers)):
                temp = values[f'input_{i}']
                if temp == '':
                    temp = 'NULL'
                update_list.append(temp)
            try:
                update_table(cursor, db, current_table, table_headers, update_list,
                             values['update_key'], values['update_keyvalue'], values['update_op'])
            except mysql.connector.errors.Error as e:
                SG.Popup(e)
            else:
                new_window = initialize_main_window(cursor, settings, current_table, all_tables,
                                                    where_clause, order_clause, limit_clause, num_rows=num_rows)
                window.close()
                window = new_window

        if event == 'DELETE':
            try:
                delete_from_table(cursor, db, current_table,
                                  values['delete_key'], values['delete_keyvalue'], values['delete_op'])
            except mysql.connector.errors.Error as e:
                SG.Popup(e)
            else:
                new_window = initialize_main_window(cursor, settings, current_table, all_tables,
                                                    where_clause, order_clause, limit_clause, num_rows=num_rows)
                window.close()
                window = new_window

        if event == 'apply_filters':
            if values['order_enable']:
                order_clause = f' ORDER BY {values["order_change"]} {values["asc_desc"]} '
            if values['limit_enable']:
                limit_clause = f' LIMIT {values["l_limit"]}, {values["r_limit"]} '
            if values['where_enable']:
                where_clause = f' WHERE {values["where_column"]} {values["where_operator"]} {values["where_value"]}'
            new_window = initialize_main_window(cursor, settings, current_table, all_tables,
                                                where_clause, order_clause, limit_clause, num_rows=num_rows)
            window.close()
            window = new_window

        if event == 'query_log':
            show_query_log()

    window.close()