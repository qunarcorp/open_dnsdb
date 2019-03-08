# -*- coding: utf-8 -*-

operation_type_dict = {
    'add_user': '用户新增',
    'delete_user': '用户删除',
    'update_user': '用户信息修改',
    'add_host': '主机新增',
    'delete_host': '主机删除',
    'update_reload_status': '主机组reload修改',
    'update_view_state': '状态修改',
    'update_view_domain': '域名修改',
    'add_view_domain': '域名新增',
    'delete_view_domain': '域名删除',
    'migrate_rooms': '机房迁移',
    'recover_rooms': '机房恢复',
    # 'onekey_recover_rooms': '一键恢复',
    # 'switch_ip_to_aqb': 'IP高防切换',
    # 'switch_ip_from_aqb': 'IP高防恢复',
    # 'replace_ip': 'IP替换',
    # 'cancel_replace_ip': 'IP替换恢复',
    'add_isp': 'ISP新增',
    'delete_isp': 'ISP删除',
    'update_zone_header': '头文件更新',
    'update_named_zone': '配置更新zone',
    'add_named_zone': '配置新增zone',
    'delete_named_zone': '配置删除zone',
    'update_named_conf_header': '配置更新named',
    'conf_deploy': '配置部署',
    'rename_subnet': '子网重命名',
    'delete_subnet': '子网删除',
    'add_subnet': '子网新增',
    'manadd_record': '记录新增',
    'delete_record': '记录删除',
    'modify_record': '记录修改',
    'autoadd_record': '记录自动绑定',
    'acl_migration': 'acl运营商迁移',
    'add_acl_subnet': 'acl网段新增',
    'delete_acl_subnet': 'acl网段删除'
    # 'modify_isp_status': 'ISP状态修改'
}


filed_dict = {
    # user
    'username': '用户名',
    'role': '角色',
    'email': '邮箱',
    # isp
    'ename': '英文名',
    'cname': '中文名',
    'abbr': '别名',
    # view
    'rooms': '机房',
    'isps': '运营商'
}
