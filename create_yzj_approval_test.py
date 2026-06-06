#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云之家审批流程创建测试脚本
================================

你现在只需要准备两个文件放在同一个文件夹：

1. create_yzj_approval_test.py
   当前这个 Python 脚本。

2. token.txt
   里面可以放两种内容之一：

   A. 获取 accessToken 的 URL，也就是你现在已有的这种：
      https://yunzhijia.com/gateway/oauth2/token/getAccessToken?appId=...&timestamp={{$microTimestamp}}&scope=team

      脚本会自动把 {{$microTimestamp}} 替换成“当前毫秒时间戳”，
      然后请求这个 URL，从返回 JSON 的 data.accessToken 中取出真正的 accessToken。

   B. 真正的 accessToken 字符串：
      如果你已经手动请求过 token 接口，也可以把返回的 data.accessToken 单独复制到 token.txt。
      脚本发现 token.txt 不是 http URL 时，会把它当成真正的 accessToken 使用。

3. approval_rows.json
   可选，多行明细文件。传入 --rows-file approval_rows.json 后，
   脚本会把 JSON 数组里的每个对象转换成 Dd_0 的一行明细。

运行方式：

    python create_yzj_approval_test.py --dry-run

    上面这条只预览 createInst 请求体，不会真的发起审批。

    python create_yzj_approval_test.py --show-template

    上面这条会调用 viewFormDef 接口，查看当前模板真实字段。
    如果流程能创建但表单为空，最应该先跑这一条。

    python create_yzj_approval_test.py

    上面这条会真正调用云之家 createInst 接口，发起一条测试审批。

    python create_yzj_approval_test.py --rows-file approval_rows.json

    上面这条会读取 approval_rows.json，一次发起多行明细。

当前模板的用车字段不是主表字段，而是在明细控件 Dd_0 里面。
所以脚本会把用车数据放到：

    details -> Dd_0 -> widgetValue -> 第 1 行

主表 widgetValue 里只放标题、备注等主表字段。

注意：

- 本脚本只使用 Python 标准库，不需要安装 requests。
- 当前提交的是 Dd_0 明细控件中的一行用车测试数据。
- createInst 返回 success=true 只代表接口收到了请求，最终还要去云之家页面核对字段是否真的显示。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


# =========================
# 一、固定配置区
# =========================

# 云之家审批模板 formCodeId。
# 你已经确认要用这个模板：“申请使用国顺司车辆测试”。
FORM_CODE_ID = "0e1d321692a9441fa24db3bb3776a7d9"

# 本次测试指定的发起人 openid。
# createInst 请求体里的 creator 会使用这个值。
CREATOR_OPENID = "5b078855e4b098424c8c3f7f"

# createInst 接口地址。
# 注意：accessToken 不放在 body 里，而是拼在 URL query 参数里：
# https://www.yunzhijia.com/.../createInst?accessToken=真正的accessToken
CREATE_INST_URL = "https://www.yunzhijia.com/gateway/workflow/form/thirdpart/createInst"

# 获取模板定义接口。
# 官方文档名称：获取表单模板接口 viewFormDef。
# 作用：根据 formCodeId 查看这个模板真实有哪些控件、控件 codeId 是什么、标题是什么。
# 当 createInst 返回成功但页面字段为空时，优先用这个接口确认 codeId。
VIEW_FORM_DEF_URL = "https://www.yunzhijia.com/gateway/workflow/form/thirdpart/viewFormDef"

# 默认读取同目录下的 token.txt。
# token.txt 可以放“获取 token 的 URL”，也可以放“真正的 accessToken”。
DEFAULT_TOKEN_FILE = "token.txt"

# 多行明细 JSON 示例文件名。
DEFAULT_ROWS_FILE = "approval_rows.json"

# 当前模板真实字段来自 viewFormDef：
# 主表只有标题、备注、图片、附件等字段；用车字段都在 Dd_0 明细中。
DETAIL_CODE_ID = "Dd_0"


# =========================
# 二、HTTP 工具函数
# =========================

def read_json_response(request: urllib.request.Request, timeout: int = 30) -> dict:
    """
    发送 HTTP 请求，并把响应解析成 JSON 字典。

    这里统一处理三类问题：
    1. HTTP 状态码不是 2xx，例如 400、401、500。
    2. 网络连接失败，例如域名访问不了。
    3. 云之家返回的内容不是 JSON。
    """
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_text}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"网络请求失败：{exc.reason}") from exc

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"响应不是 JSON，原始响应为：{raw_text}") from exc


def http_get_json_by_full_url(url: str) -> dict:
    """
    用完整 URL 发起 GET 请求。

    token.txt 里已经是完整 token 获取 URL，所以这里不再拆参数，
    只负责直接访问它。
    """
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "yunzhijia-create-inst-test/1.0"},
    )
    return read_json_response(request)


def http_post_json(url: str, query_params: dict, body: dict) -> dict:
    """
    用 JSON body 发起 POST 请求。

    createInst 的 accessToken 是 URL query 参数：
        ?accessToken=xxx

    审批数据是 JSON body：
        {
          "formCodeId": "...",
          "creator": "...",
          "widgetValue": {...}
        }
    """
    query = urllib.parse.urlencode(query_params)
    request_url = f"{url}?{query}"
    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        request_url,
        data=body_bytes,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "yunzhijia-create-inst-test/1.0",
        },
    )
    return read_json_response(request)


def view_form_def(access_token: str, form_code_id: str) -> dict:
    """
    调用官方 viewFormDef 接口，获取当前审批模板定义。

    请求地址：
        POST https://www.yunzhijia.com/gateway/workflow/form/thirdpart/viewFormDef?accessToken=xxx

    请求体：
        {"formCodeId": "模板codeId"}

    返回里重点看：
        data.formInfo.widgetMap  主表字段
        data.formInfo.detailMap  明细字段
    """
    return http_post_json(
        VIEW_FORM_DEF_URL,
        {"accessToken": access_token},
        {"formCodeId": form_code_id},
    )


# =========================
# 三、token 处理
# =========================

def replace_timestamp_placeholder(url: str) -> str:
    """
    替换 token URL 里的时间戳占位符。

    你现在 token.txt 里有：
        timestamp={{$microTimestamp}}

    但云之家文档要求的是“毫秒时间戳”，例如：
        1780000000000

    所以这里会把常见占位符统一替换成 int(time.time() * 1000)。
    """
    timestamp_ms = str(int(time.time() * 1000))
    return (
        url
        .replace("{{$microTimestamp}}", timestamp_ms)
        .replace("{{$timestamp}}", timestamp_ms)
        .replace("{timestamp}", timestamp_ms)
    )


def read_token_file(token_file: str) -> str:
    """
    读取 token.txt 内容。

    返回值可能是：
    1. 获取 accessToken 的完整 URL。
    2. 真正的 accessToken 字符串。
    """
    if not os.path.exists(token_file):
        raise RuntimeError(
            f"找不到 {token_file}。\n"
            f"请把获取 accessToken 的 URL 放到 {token_file}，或者运行时使用 --access-token 传入真实 token。"
        )

    with open(token_file, "r", encoding="utf-8") as file:
        content = file.read().strip()

    if not content:
        raise RuntimeError(f"{token_file} 是空文件，请放入 token URL 或真实 accessToken。")

    return content


def get_access_token_from_token_url(token_url: str) -> str:
    """
    请求“获取 accessToken 的 URL”，并从云之家返回里提取真正的 accessToken。

    token 接口返回示例：
        {
          "success": true,
          "errorCode": 0,
          "data": {
            "accessToken": "真正要给 createInst 用的值",
            "expireIn": 7200
          }
        }
    """
    final_url = replace_timestamp_placeholder(token_url)
    response = http_get_json_by_full_url(final_url)

    if not response.get("success"):
        raise RuntimeError("获取 accessToken 失败，云之家返回：\n" + pretty_json(response))

    access_token = (response.get("data") or {}).get("accessToken")
    if not access_token:
        raise RuntimeError("token 接口返回成功，但没有 data.accessToken：\n" + pretty_json(response))

    return access_token


def resolve_access_token(args: argparse.Namespace) -> str:
    """
    得到最终给 createInst 使用的 accessToken。

    优先级：
    1. 如果运行时传了 --access-token，就直接用它。
    2. 否则读取 token.txt。
       - token.txt 如果以 http:// 或 https:// 开头，说明它是“取 token 的 URL”。
       - token.txt 如果不是 URL，说明它可能就是“真正的 accessToken”。
    """
    if args.access_token:
        return args.access_token.strip()

    token_file_content = read_token_file(args.token_file)

    if token_file_content.startswith(("http://", "https://")):
        print("检测到 token.txt 中是获取 accessToken 的 URL，正在请求 token 接口...")
        return get_access_token_from_token_url(token_file_content)

    print("检测到 token.txt 中像是真实 accessToken，将直接用于 createInst...")
    return token_file_content


# =========================
# 四、createInst 请求体
# =========================

def build_widget_value(args: argparse.Namespace) -> dict:
    """
    组装主表 widgetValue。

    这次问题的根因是：用车方、联系人、出发地点等字段都不是主表字段，
    它们在 Dd_0 明细控件里。主表这里只提交真正属于主表的字段。
    """
    return {
        "_S_TITLE": args.title,
        "Ta_1": args.remark,
    }


def build_detail_row(args: argparse.Namespace, row_id: str = "1") -> dict:
    """
    组装 Dd_0 明细中的一行。

    官方 createInst 文档要求明细字段放在 details 中：

        "details": {
            "Dd_0": {
                "widgetValue": [
                    {
                        "_id_": "1",
                        "Te_0": "用车方",
                        "Nu_0": "1"
                    }
                ]
            }
        }

    注意：
    - _id_ 必填，值为字符串数字，一般从 "1" 开始。
    - textWidget 传字符串。
    - Nu_0 是 numberWidget，官方文档也要求数字/金额按字符串传。
    """
    return {
        "_id_": row_id,
        "Te_0": args.client_name,
        "Te_1": f"{args.contact_name} {args.contact_phone}".strip(),
        "Te_2": args.departure,
        "Te_3": args.destination,
        "Te_4": args.plate_number,
        "Te_5": args.driver_name,
        "Te_6": args.departure_time,
        "Te_7": args.return_time,
        "Te_8": args.vehicle_type,
        "Te_9": args.mileage,
        "Te_10": args.rental_fee,
        "Te_11": args.fuel_fee,
        "Te_12": args.bridge_fee,
        "Te_13": args.labor_fee,
        "Te_14": args.estimated_cost,
        "Te_15": args.estimated_profit,
        "Nu_0": args.rental_days,
    }


def first_value(row: dict, *keys: str, default: str = "") -> str:
    """
    从一行 JSON 中按多个别名取值。

    例如油电费字段，文件里可以写：
      fuel_fee
      oil_electric_fee
      Te_11

    只要其中一个有值，就会被拿来填到云之家的 Te_11。
    """
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value)
    return default


def build_detail_row_from_file(args: argparse.Namespace, row: dict, row_id: str) -> dict:
    """
    把 approval_rows.json 中的一条业务数据转换成 Dd_0 的一行明细。

    支持两种写法：
    1. 业务字段名：client_name、departure、rental_fee 等。
    2. 云之家 codeId：Te_0、Te_1、Nu_0 等。

    如果某个字段没写，会用命令行默认值兜底。
    """
    contact = first_value(row, "contact", "Te_1")
    if not contact:
        contact_name = first_value(row, "contact_name", default=args.contact_name)
        contact_phone = first_value(row, "contact_phone", default=args.contact_phone)
        contact = f"{contact_name} {contact_phone}".strip()

    return {
        "_id_": str(row.get("_id_", row_id)),
        "Te_0": first_value(row, "client_name", "client_company", "Te_0", default=args.client_name),
        "Te_1": contact,
        "Te_2": first_value(row, "departure", "Te_2", default=args.departure),
        "Te_3": first_value(row, "destination", "Te_3", default=args.destination),
        "Te_4": first_value(row, "plate_number", "vehicle_plate", "Te_4", default=args.plate_number),
        "Te_5": first_value(row, "driver_name", "driver", "Te_5", default=args.driver_name),
        "Te_6": first_value(row, "departure_time", "start_time", "Te_6", default=args.departure_time),
        "Te_7": first_value(row, "return_time", "end_time", "Te_7", default=args.return_time),
        "Te_8": first_value(row, "vehicle_type", "Te_8", default=args.vehicle_type),
        "Te_9": first_value(row, "mileage", "Te_9", default=args.mileage),
        "Te_10": first_value(row, "rental_fee", "Te_10", default=args.rental_fee),
        "Te_11": first_value(row, "fuel_fee", "oil_electric_fee", "Te_11", default=args.fuel_fee),
        "Te_12": first_value(row, "bridge_fee", "toll_fee", "Te_12", default=args.bridge_fee),
        "Te_13": first_value(row, "labor_fee", "driver_labor_fee", "Te_13", default=args.labor_fee),
        "Te_14": first_value(row, "estimated_cost", "expected_cost", "Te_14", default=args.estimated_cost),
        "Te_15": first_value(row, "estimated_profit", "Te_15", default=args.estimated_profit),
        "Nu_0": first_value(row, "rental_days", "days", "Nu_0", default=args.rental_days),
    }


def read_rows_file(rows_file: str) -> list[dict]:
    """
    读取多行明细 JSON 文件。

    文件格式必须是数组：
        [
          {"client_name": "客户A"},
          {"client_name": "客户B"}
        ]
    """
    with open(rows_file, "r", encoding="utf-8") as file:
        rows = json.load(file)

    if not isinstance(rows, list):
        raise RuntimeError(f"{rows_file} 顶层必须是 JSON 数组。")

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise RuntimeError(f"{rows_file} 第 {index} 行不是 JSON 对象。")

    if not rows:
        raise RuntimeError(f"{rows_file} 不能为空数组。")

    return rows


def build_details(args: argparse.Namespace) -> dict:
    """组装 createInst 的 details 明细表字段。"""
    if args.rows_file:
        rows = read_rows_file(args.rows_file)
        detail_rows = [
            build_detail_row_from_file(args, row, str(index))
            for index, row in enumerate(rows, start=1)
        ]
    else:
        detail_rows = [build_detail_row(args, "1")]

    return {
        DETAIL_CODE_ID: {
            "widgetValue": detail_rows,
        },
    }


def build_create_inst_body(args: argparse.Namespace) -> dict:
    """
    组装 createInst 的 JSON body。

    关键字段说明：

    formCodeId:
        审批模板 ID，这里用“申请使用国顺司车辆测试”的模板。

    creator:
        发起人 openid，这里用你指定的 6645b8b57e94ac00013db4bf。

    skipWidgetAuthorityCheck:
        跳过字段权限校验。第三方接口发起时一般建议传 true。

    requestId:
        本次请求的唯一 ID，用 uuid 自动生成，避免云之家重复提交判断混乱。

    widgetValue:
        表单字段值。
    """
    return {
        "formCodeId": args.form_code_id,
        "creator": args.creator,
        "skipWidgetAuthorityCheck": True,
        "useAlias": False,
        "requestId": str(uuid.uuid4()),
        "widgetValue": build_widget_value(args),
        "details": build_details(args),
    }


def print_template_summary(response: dict) -> None:
    """
    把 viewFormDef 的返回结果整理成人能看的字段清单。

    这样你不用在一大段 JSON 里找字段：
    - 主表字段：codeId / title / type
    - 明细字段：明细 codeId，以及明细子字段 codeId / title / type
    """
    print("\n云之家 viewFormDef 返回：")
    print(pretty_json(response))

    if not response.get("success"):
        print("\n获取模板失败，请先看上面的 error/errorCode。")
        return

    form_info = ((response.get("data") or {}).get("formInfo") or {})
    widget_map = form_info.get("widgetMap") or {}
    detail_map = form_info.get("detailMap") or {}

    print("\n主表字段清单：")
    if not widget_map:
        print("  没有拿到 widgetMap。")
    else:
        for code_id, widget in widget_map.items():
            title = widget.get("title")
            widget_type = widget.get("type")
            print(f"  {code_id}\t{title}\t{widget_type}")

    print("\n明细字段清单：")
    if not detail_map:
        print("  这个模板没有明细控件，或者接口没有返回 detailMap。")
    else:
        for detail_code_id, detail in detail_map.items():
            detail_title = detail.get("title")
            detail_type = detail.get("type")
            print(f"  明细：{detail_code_id}\t{detail_title}\t{detail_type}")

            widget_vos = detail.get("widgetVos") or {}
            for child_code_id, child in widget_vos.items():
                child_title = child.get("title")
                child_type = child.get("type")
                print(f"    子字段：{child_code_id}\t{child_title}\t{child_type}")


# =========================
# 五、命令行参数
# =========================

def parse_args() -> argparse.Namespace:
    """
    命令行参数。

    你最常用的只有两个：

        python create_yzj_approval_test.py --dry-run
        python create_yzj_approval_test.py

    其他参数只是为了临时替换测试数据，不改代码也能换字段。
    """
    parser = argparse.ArgumentParser(description="创建云之家审批流程测试")

    # 只预览 createInst 请求体，不真正提交。
    parser.add_argument("--dry-run", action="store_true", help="只打印 createInst 请求体，不真正提交")

    # 只查看模板字段，不创建审批。
    parser.add_argument("--show-template", action="store_true", help="调用 viewFormDef 查看模板真实字段，不创建审批")

    # token.txt 文件路径，默认读取当前目录下 token.txt。
    parser.add_argument("--token-file", default=DEFAULT_TOKEN_FILE, help="保存 token URL 或真实 accessToken 的文件")

    # 多行明细 JSON 文件。传入后会一次提交多条 Dd_0 明细。
    parser.add_argument("--rows-file", default="", help=f"多行明细 JSON 文件，例如 {DEFAULT_ROWS_FILE}")

    # 如果你已经拿到真正的 accessToken，可以直接传这个参数，脚本就不会读取 token.txt。
    parser.add_argument("--access-token", default="", help="真实 accessToken；传入后会跳过 token.txt")

    # 模板和发起人，默认已经按你本次需求写好。
    parser.add_argument("--form-code-id", default=FORM_CODE_ID, help="审批模板 formCodeId")
    parser.add_argument("--creator", default=CREATOR_OPENID, help="发起人 openid")
    # 兼容旧参数。现在已经确认字段在 Dd_0 明细里，
    # 所以这两个排查参数不再影响请求体。
    parser.add_argument("--value-mode", default="raw", help=argparse.SUPPRESS)
    parser.add_argument("--field-key-mode", default="codeid", help=argparse.SUPPRESS)

    # 下面都是测试表单字段。需要换测试数据时，可以通过命令行覆盖。
    parser.add_argument("--title", default=f"包车审批接口测试-{time.strftime('%Y%m%d-%H%M%S')}")
    parser.add_argument("--remark", default="接口创建审批测试")
    parser.add_argument("--client-name", default="接口测试用车方")
    parser.add_argument("--contact-name", default="接口测试联系人")
    parser.add_argument("--contact-phone", default="15875020057")
    parser.add_argument("--departure", default="义祠")
    parser.add_argument("--destination", default="广州天河城")
    parser.add_argument("--vehicle-type", default="商务车(7座)")
    parser.add_argument("--plate-number", default="粤C11111")
    parser.add_argument("--driver-name", default="张师傅")
    parser.add_argument("--departure-time", default="2026-05-28 09:00")
    parser.add_argument("--return-time", default="2026-05-28 18:00")
    parser.add_argument("--rental-days", default="1")
    parser.add_argument("--mileage", default="300")
    parser.add_argument("--rental-fee", default="1300")
    parser.add_argument("--fuel-fee", default="100")
    parser.add_argument("--bridge-fee", default="130")
    parser.add_argument("--labor-fee", default="400")
    parser.add_argument("--estimated-cost", default="630")
    parser.add_argument("--estimated-profit", default="670")

    return parser.parse_args()


# =========================
# 六、主流程
# =========================

def pretty_json(data: dict) -> str:
    """把字典格式化成中文可读的 JSON。"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def main() -> int:
    """
    主流程：

    1. 读取命令行参数。
    2. 组装 createInst 请求体。
    3. 如果是 --dry-run，只打印请求体后退出。
    4. 获取真正的 accessToken。
    5. 如果是 --show-template，只查看模板字段后退出。
    6. POST 调用 createInst。
    7. 打印云之家返回结果，尤其是 flowInstId / formInstId。
    """
    args = parse_args()
    create_inst_body = build_create_inst_body(args)

    if args.dry_run:
        print("这是 createInst 请求体预览，不会真的发起审批：")
        print(pretty_json(create_inst_body))
        return 0

    access_token = resolve_access_token(args)

    if args.show_template:
        print("正在调用 viewFormDef 获取模板真实字段...")
        response = view_form_def(access_token, args.form_code_id)
        print_template_summary(response)
        return 0 if response.get("success") else 1

    print("正在调用 createInst 创建审批流程...")
    print("提交格式：主表 widgetValue + 明细 details.Dd_0.widgetValue")
    response = http_post_json(
        CREATE_INST_URL,
        {"accessToken": access_token},
        create_inst_body,
    )

    print("\n云之家 createInst 返回：")
    print(pretty_json(response))

    if response.get("success") and response.get("errorCode") == 0:
        data = response.get("data") or {}
        print("\n创建成功。请到云之家审批详情中检查字段是否显示。")
        print(f"flowInstId: {data.get('flowInstId')}")
        print(f"formInstId: {data.get('formInstId')}")
        return 0

    print("\n创建失败或返回非成功状态，请根据上面的 error/errorCode 排查。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
