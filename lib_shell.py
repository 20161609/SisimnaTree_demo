import lib_sanitizer as st
from lib_make_excel import AccountBookGenerator, ExpandTreeGenerator
import calendar
import lib_branch as br
import lib_database as dbl
from lib_tree_editor import TreeEditor
from lib_insert_transaction import ImageSaver
from lib_delete_transaction import delete_transaction
from lib_modify_transaction import ImageBrowser
from lib_pdf_image import generate_image_pdf

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from prettytable import PrettyTable
from datetime import datetime, timedelta
import os

DATABASE_NAME = "accountBook.db"
quit_commands = {'q!', 'Q!', 'quit', 'QUIT'}


def create_graph(results, data_type):
    plt.style.use('dark_background')

    months = [result[0] for result in results]
    fig, ax = plt.subplots()

    colors = {'IN': 'lightgreen', 'OUT': 'salmon', 'BALANCE': 'skyblue'}
    if data_type == 'BALANCE':
        balances = [inflow - outflow for _, inflow, outflow in results]
        label = 'Balance'
        ax.bar(months, balances, color=colors[data_type], label=label)
    else:
        amounts = [amount for _, amount in results]
        label = 'Cash In' if data_type == 'IN' else 'Cash Out'
        ax.bar(months, amounts, color=colors[data_type], label=label)

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Amount (₩)', fontsize=12)
    ax.set_title(f'Monthly {label}', fontsize=14)
    ax.legend()

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def display_help():
    # Input
    pass


class Shell:
    def __init__(self):
        self.prompt = "$[~Home/]>> "  # 프롬프트 메시지 (현 브랜치 기반)
        self.db = None
        self.root = None
        self.branch = None
        self.synchronization_tree()
        self.synchronization_db()

    # 유저 커맨드 실행
    def fetch(self, command):
        try:
            list_cmd = command.split()
            if list_cmd[0] in {'chdir', 'cd'} and len(list_cmd) == 2:
                self.chdir(list_cmd)
            elif list_cmd[0] in {'insert', 'in'} and len(list_cmd) == 1:
                self.insert_transaction()
            elif list_cmd[0] in {'delete', 'del'} and len(list_cmd) == 1:
                self.delete_transaction()
            elif list_cmd[0] in {'modify', 'mod'} and len(list_cmd) == 1:
                self.modify_transactions()
            elif list_cmd[0] in {'list', 'ls'} and len(list_cmd) == 1:
                self.listdir()
            elif list_cmd[0] in {'refer', 'rf'} and len(list_cmd) > 1:
                self.refer(list_cmd)
            elif list_cmd[0] in {'graph', 'gr'} and 1 <= len(list_cmd) < 3:
                self.graph(list_cmd)
            elif list_cmd[0] in {'excel', 'xl'} and len(list_cmd) == 2:
                self.display_excel(list_cmd)
            elif list_cmd[0] == 'help' and len(list_cmd) == 1:
                display_help()
            elif list_cmd[0] in {'report', 'rp'} and len(list_cmd) == 1:
                self.report_generator()
            elif list_cmd[0] in {'sync', 'synchronization'} and len(list_cmd) == 1:
                self.synchronization_db()
            elif list_cmd[0] in {'tree', 'tr'} and len(list_cmd) == 1:
                self.tree()
            elif list_cmd[0] in {'expand', 'ex', 'ep'} and len(list_cmd) == 1:
                self.expand_tree()


        except Exception as e:
            print('!Error:', e)
            pass

    # 트랜젝션 컨트롤러
    def synchronization_db(self):
        self.db = dbl.DatabaseController()

    def synchronization_tree(self):
        json_tree = br.load_tree()
        root = br.build_tree_from_json(json_tree)
        self.root = root
        self.branch = self.root

    def insert_transaction(self):
        print('...Inserting Transaction')
        ImageSaver(self.synchronization_db, self.branch.path.replace('-', '/'))

    def delete_transaction(self):
        print('...Deleting Transaction')
        delete_transaction(self.synchronization_db, self.branch.path.replace('-', '/'))
        return

    # 브랜치 이동
    def chdir(self, command: list):
        # 1. 타깃 브랜치 추적
        if len(command) == 1:
            command.append('')

        n, target = 0, command[1]
        if not target in self.branch.children:
            if target.isdigit():
                index = int(target) - 1
                if not (0 <= index < len(self.branch.children)):
                    print("!Error: Not valid path")
                    print("...")
                    return
                target = list(self.branch.children.keys())[index]

        while target.startswith('../'):
            n += 1
            target = target.lstrip('.').lstrip('/')

        navigating = self.branch
        for i in range(n):
            if navigating == self.root:
                break
            navigating = navigating.parent

        # 2. 타깃 브랜치로 이동
        try:
            if n == 0 and (target == '' or target == '-'):  # navigate to HOME
                self.branch = self.root
            elif n == 0 and target.split('/')[0] == 'Home':  # navigate to an address referenced from HOME
                new_target = "/".join(target.split('/')[1::])
                navigating = br.search_branch(self.root, new_target)
                if navigating:
                    self.branch = navigating
                else:
                    print("!Error: Not valid path")
                    print("...")
            elif n > 0 and target == '':  # navigate to an address referenced from current Branch (depth > 1)
                self.branch = navigating
            else:  # navigate to an address referenced from HOME (depth == 1)
                navigating = br.search_branch(navigating, target)
                if navigating:
                    self.branch = navigating
                else:
                    print("!Error: Not valid path")
                    print("...")

            # 3. 프롬프트 메시지 업데이트
            self.prompt = f"$[~{self.branch.path}]>> "
        except Exception as e:
            print(e)

    # 자식 브랜치 출력
    def listdir(self):
        for i, child in enumerate(self.branch.children):
            print("{}. {}".format(i + 1, child))
        print('...')

    # 회계 장부 출력 (일별, 월별, 브랜치 별)
    def refer(self, list_cmd: list):
        if list_cmd[1] == '-d':  # 일별
            self.refer_daily(list_cmd)
        elif list_cmd[1] == '-m':  # 월별
            self.refer_monthly(list_cmd)
        elif list_cmd[1] == '-t':  # 브랜치 별
            self.refer_tree(list_cmd)

    # 일별 날짜 단위, 회계 장부 출력
    def refer_daily(self, list_cmd: list):
        # 날짜 변수
        begin_date, end_date = "0001-01-01", "9999-12-31"
        if len(list_cmd) == 3:
            begin, end = list_cmd[2].split('~')
            if begin != '':
                begin_date = st.format_date(begin)
            if end != '':
                end_date = st.format_date(end)

            # 잘못된 날짜 입력시, 에러메시지 반환
            if (begin_date is None) or (end_date is None):
                print("!Error: NOT valid Date Input")
                print("...")
                return

        # Database 조회
        daily_box = dbl.make_daily_box(self.branch, self.db, [begin_date, end_date])

        # 테이블 출력
        table = PrettyTable()
        table.field_names = ['DATE', 'BRANCH', 'IN', 'OUT', 'BALANCE', 'DESCRIPTION']
        count, balance = 0, 0
        total_in, total_out = 0, 0
        for row in daily_box:
            count += 1
            r_date, r_branch, r_cashflow, r_desc = row
            r_date = r_date.split()[0]

            _in = st.format_cost(r_cashflow) if r_cashflow > 0 else '-'
            _out = st.format_cost(-r_cashflow) if r_cashflow <= 0 else '-'

            total_in += max(r_cashflow, 0)
            total_out += -min(r_cashflow, 0)

            balance = total_in - total_out
            new_row = (r_date, r_branch, _in, _out, st.format_cost(balance), r_desc)
            table.add_row(new_row)
        print(table)

        # 요약
        print("\n*** Summary ***")
        print("- Branch: {}".format(self.branch.path))
        print("- Period: {} ~ {}".format(begin_date, end_date))
        print("- Count: {}".format(count))
        print("- Total In: {}".format(st.format_cost(total_in)))
        print("- Total Out: {}".format(st.format_cost(total_out)))
        print("- Balance: {}".format(st.format_cost(balance)))
        print()

    # 월별 날짜 단위, 회계 장부 출력
    def refer_monthly(self, list_cmd: list):
        # 날짜 변수
        begin_date, end_date = "0001-01-01", "9999-12-31"
        if len(list_cmd) == 3:
            begin, end = list_cmd[2].split('~')
            if begin != '':
                begin_date = st.format_date(begin)
            if end != '':
                end_date = st.format_date(end)
            # 잘못된 날짜 입력시, 에러메시지 반환
            if (begin_date is None) or (end_date is None):
                print("!Error: NOT valid Date Input")
                print("...")
                return

        # 월별 리스트
        monthly_box = dbl.make_monthly_box(self.branch, self.db, [begin_date, end_date])

        # 테이블 출력
        table = PrettyTable()
        table.field_names = ['MONTHLY', 'IN', 'OUT', 'BALANCE']
        total_in, total_out, balance = 0, 0, 0
        for row in monthly_box:
            monthly, _in, _out = row
            total_in += _in
            total_out += -_out
            balance = (total_in - total_out)

            _in = st.format_cost(_in) if _in != 0 else '-'
            _out = st.format_cost(-_out) if _out != 0 else '-'

            new_row = (monthly, _in, _out, st.format_cost(balance))
            table.add_row(new_row)
        print(table)
        print()

        # 요약
        print("*** Summary ***")
        print("- Branch: {}".format(self.branch.path))
        print("- Period: {} ~ {}".format(begin_date, end_date))
        print("- Total In: {}".format(st.format_cost(total_in)))
        print("- Total Out: {}".format(st.format_cost(total_out)))
        print("- Balance: {}".format(st.format_cost(balance)))
        print()

    # 브랜치 단위, 트리 구조 출력
    def refer_tree(self, command: list):
        # 1. 조상 노드 생성
        cost_sums = {'Home': {'IN': 0, 'OUT': 0}}  # dictionary of each node's sum

        # 2. 기간 설정
        begin_date, end_date = '0000-01-01', '9999-12-31'

        if len(command) == 3:
            begin, end = command[2].split('~')
            if begin != '':
                begin_date = st.format_date(begin)
            if end != '':
                end_date = st.format_date(end)
            if (begin_date is None) or (end_date is None):
                print("!Error: NOT valid Date Input")
                print("...")
                return
        elif len(command) > 3:
            print("!Error: Too many parameters")
            print("...")
            return

        # 3. 빈 노드 채우기
        # 3.1. 모든 트랜젝션 불러오기
        sql_query = f"SELECT _Branch, _CashFlow FROM {self.db.table_name}"
        sql_query += " WHERE _Branch LIKE '{}%'".format(self.branch.path)
        sql_query += " AND '{}' <= _Date AND _Date <= '{}'".format(begin_date, end_date)

        self.db.cursor.execute(sql_query)
        res = self.db.cursor.fetchall()

        # 3.2. 기록
        for node_path, cost in res:
            cur_node = self.branch.path
            if not cur_node in cost_sums:
                cost_sums[cur_node] = {'IN': 0, 'OUT': 0}

            children_path = node_path.split(self.branch.path)[1]
            if cost > 0:
                cost_sums[cur_node]['IN'] += cost
            else:
                cost_sums[cur_node]['OUT'] -= cost

            for node in children_path.split('/'):
                if node == '':
                    continue
                cur_node += '/{}'.format(node)
                if not cur_node in cost_sums:
                    cost_sums[cur_node] = {'IN': 0, 'OUT': 0}

                if cost > 0:
                    cost_sums[cur_node]['IN'] += cost
                else:
                    cost_sums[cur_node]['OUT'] -= cost

        # 4. 재무 트리 출력
        def dfs_display(branch: br.Branch, depth: int):
            if branch.path in cost_sums:
                total_in = cost_sums[branch.path]['IN']
                total_out = cost_sums[branch.path]['OUT']
            else:
                total_in, total_out = 0, 0
            branch_shape = '│    ' * depth + '└── '
            total_balance = st.format_cost(total_in - total_out)
            total_in = st.format_cost(total_in)
            total_out = st.format_cost(total_out)
            summary = "in:{}, out:{}, bal: {}".format(total_in, total_out, total_balance)
            print("{}{}[{}]".format(branch_shape, branch.name, summary))

            for child in branch.children:
                child_branch = branch.children[child]
                dfs_display(child_branch, depth + 1)

        dfs_display(self.branch, 0)
        print("...")
        return

    # 그래프 출력
    def graph(self, list_cmd):
        if len(list_cmd) > 1:
            if list_cmd[1] == 'in':
                data_type = 'IN'
            elif list_cmd[1] == 'out':
                data_type = 'OUT'
            elif list_cmd[1] == 'bal':
                data_type = 'BALANCE'
            else:
                return
        else:
            return

        begin_date, end_date = '0001-01-01', '9999-12-31'
        if len(list_cmd) > 2 and len(list_cmd[2]) != 2:
            begin, end = list_cmd[2].split('~')
            begin_date = st.format_date(begin) if begin else begin_date
            end_date = st.format_date(end) if end else end_date
            if (begin_date is None) or (end_date is None):
                print("!Error: NOT valid Date Input")
                print("...")
                return

        graph_box = dbl.make_graph_box(self.branch, self.db, [begin_date, end_date], data_type)

        # 그래프 생성
        create_graph(graph_box, data_type)

    # 엑셀 출력
    def display_excel(self, list_cmd: list):
        if list_cmd[1] == '-d':  # 일별 엑셀 데이터
            self.excel_daily(list_cmd)
        elif list_cmd[1] == '-m':  # 월별 엑셀 데이터
            self.excel_monthly(list_cmd)

    # 일별 엑셀 데이터 출력
    def excel_daily(self, list_cmd: list):
        # 날짜 변수
        begin_date, end_date = "0001-01-01", "9999-12-31"
        if len(list_cmd) == 3:
            begin, end = list_cmd[2].split('~')
            if begin != '':
                begin_date = st.format_date(begin)
            if end != '':
                end_date = st.format_date(end)

            # 잘못된 날짜 입력시, 에러 메시지 반환
            if (begin_date is None) or (end_date is None):
                print("!Error: NOT valid Date Input")
                print("...")
                return

        # Database 조회
        daily_box = dbl.make_daily_box(self.branch, self.db, [begin_date, end_date])

        # 엑셀 출력
        headers = ['DATE', 'BRANCH', 'IN', 'OUT', 'BALANCE', 'DESCRIPTION']
        xl_generator = AccountBookGenerator(daily_box, headers)

        os.makedirs('datas', exist_ok=True)

        time = str(datetime.now().timestamp()).replace('.', '_')
        file_path = f'datas/daily_{time}.xlsx'
        xl_generator.make_excel(file_path)

    # 월별 엑셀 데이터 출력
    def excel_monthly(self, list_cmd: list):
        begin_date, end_date = '0001-01-01', '9999-12-31'
        if len(list_cmd) == 3:
            # 기간 입력 유효성 검사
            begin, end = list_cmd[2].split('~')
            if begin != '':
                begin_date = st.format_date(begin)
            if end != '':
                end_date = st.format_date(end)
            if (begin_date is None) or (end_date is None):
                print("!Error: NOT valid Date Input")
                print("...")
                return

        monthly_box = dbl.make_monthly_box(self.branch, self.db, [begin_date, end_date])
        headers = ['MONTHLY', 'IN', 'OUT', 'BALANCE']
        xl_generator = AccountBookGenerator(monthly_box, headers)

        os.makedirs('datas', exist_ok=True)
        time = str(datetime.now().timestamp()).replace('.', '_')
        file_path = f'datas/monthly_{time}.xlsx'
        xl_generator.make_excel(file_path)

    def tree(self):
        if self.branch.path != self.root.path:
            print('!Error:', "Home 디렉토리에서 실행해야 합니다")
        else:
            TreeEditor(self.synchronization_tree)

    def modify_transactions(self):
        ImageBrowser(self.branch.path.replace('-', '/'), self.synchronization_db)

    def report_generator(self):
        # Input Begin Date
        begin_date = input('Input Begin Date (YYYY-MM-DD): ')
        if begin_date == '':
            begin_date = '0000-01-01'
        else:
            begin_date = st.format_date(begin_date)
            if begin_date is None:
                print('!Error:', 'Not valid date format..(begin input)')
                return

        # Input End Date
        end_date = input('Input End Date (YYYY-MM-DD): ')
        if end_date == '':
            end_date = '9999-12-31'
        else:
            end_date = st.format_date(end_date)
            if end_date is None:
                print('!Error:', 'Not valid date format..(end input)')
                return

        # Input Interval Month
        try:
            interval = int(input('Input the number of months per grouping: '))
            if interval <= 0:
                print('!Error:', 'you must input n > 0 in interval month..')
                return
        except Exception as e:
            print('!Error:', e)
            return

        # SQL 쿼리 구성
        sql_query = f"""
            SELECT _Date, _Branch, _CashFlow, _Description 
            FROM {self.db.table_name}
            WHERE (_Date BETWEEN '{begin_date}' AND '{end_date}') AND _Branch LIKE '{self.branch.path}%'
            ORDER BY _Date
        """
        self.db.cursor.execute(sql_query)
        transactions = self.db.cursor.fetchall()

        if not transactions:
            print("...No transactions found in the given date range.")
            return

        begin_y, begin_m, begin_d = map(int, begin_date.split('-'))
        end_y, end_m, end_d = map(int, end_date.split('-'))
        cur_y, cur_m, cur_d = begin_y, begin_m, begin_d

        def value_to_date(yy, mm, dd):
            date_int = yy * 10000 + mm * 100 + dd
            return f'{str(date_int)[:4:]}-{str(date_int)[4:6:]}-{str(date_int)[6::]}'

        def get_next_date(yy, mm, dd, interval):
            return yy if mm + interval <= 12 else yy + 1, mm + interval if mm + interval <= 12 else mm + interval - 12, 1

        receipt_index = 0
        page_box = {}
        while value_to_date(cur_y, cur_m, cur_d) <= end_date and receipt_index < len(transactions):
            nxt_y, nxt_m, nxt_d = get_next_date(cur_y, cur_m, cur_d, interval)
            nxt_date = min(value_to_date(nxt_y, nxt_m, nxt_d), end_date)

            _date, _branch, _cashflow, _description = transactions[receipt_index]
            if _date >= nxt_date:
                cur_y, cur_m, cur_d = nxt_y, nxt_m, nxt_d
            else:
                key = f'{value_to_date(cur_y, cur_m, cur_d)}~{nxt_date}'
                if not key in page_box:
                    page_box[key] = []

                page_box[key].append(transactions[receipt_index])
                receipt_index += 1

        time = str(datetime.now().timestamp()).replace('.', '_')
        dir_path = f'datas/{self.branch.path}_report_{time}'
        os.makedirs(dir_path, exist_ok=True)

        headers = ['DATE', 'BRANCH', 'IN', 'OUT', 'BALANCE', 'DESCRIPTION']
        for key in page_box:
            file_path = dir_path + '/' + key

            # 엑셀 장부 출력
            xl_generator = AccountBookGenerator(page_box[key], headers)
            xl_generator.make_excel(file_path + '.xlsx')

            # 영수증 출력
            image_box = []
            for _date, _branch, _cashflow, _description in page_box[key]:
                info = st.make_image_file_name(_date, _branch, _cashflow, _description)

                if info['status']:
                    for a in ['.png', '.jpg', '.jpeg']:
                        image_path = f"transactions/{info['tag']}" + a
                        if os.path.exists(image_path):
                            image_box.append(image_path)

            generate_image_pdf(image_box, file_path + '.pdf')

    def expand_tree(self):
        # 기간 입력
        begin_month = input('Input Begin Month.. (YYYY-MM)').strip()
        if begin_month == '':
            _now = datetime.now()
            begin_month = st.format_month(f'{_now.year}-{_now.month}')
        else:
            begin_month = st.format_month(begin_month)

        end_month = input('Input End Month.. (YYYY-MM)').strip()
        if end_month == '':
            _now = datetime.now()
            end_month = st.format_month(f'{_now.year}-{_now.month}')
        else:
            end_month = st.format_month(end_month)

        if begin_month > end_month:
            print('!Error', 'The Input(Month) must be that Begin Month <= End Month')
            return

        begin_date = begin_month + '-01'
        end_y, end_m = map(int, end_month.split('-'))
        end_day = calendar.monthrange(end_y, end_m)[1]
        end_date = end_month + '-' + f'{end_day + 100}'[1::]

        # db 조회
        transactions = dbl.make_daily_box(self.branch, self.db, [begin_date, end_date])

        if len(transactions) == 0:
            print("!Error", f"There s no transaction in ('{begin_month}'~'{end_month}')")
            return

        # 엑셀 시트 출력
        etg = ExpandTreeGenerator(self.branch, [begin_month, end_month])
        etg.make_account_book(transactions)
        etg.make_excel('datas/abc_in.xlsx', 'datas/abc_out.xlsx')
