# encoding: utf-8
"""Internationalization support for Ansys Material Database."""
from __future__ import annotations

SUPPORTED_LANGUAGES = {"en": "English", "zh": "中文"}

SUPPORTED_LANGUAGES = {"en": "English", "zh": "中文"}

_TRANSLATIONS = {
    'app.title': {"en": 'Ansys Material Database', "zh": '材料数据库'},
    'ok': {"en": 'OK', "zh": '确定'},
    'cancel': {"en": 'Cancel', "zh": '取消'},
    'save': {"en": 'Save', "zh": '保存'},
    'close': {"en": 'Close', "zh": '关闭'},
    'about.title': {"en": 'About', "zh": '关于'},
    'about.text': {"en": 'Ansys Material Database v{version}', "zh": 'Ansys 材料数据库 v{version}'},
    'menu.file': {"en": 'File', "zh": '文件'},
    'menu.view': {"en": 'View', "zh": '视图'},
    'menu.tools': {"en": 'Tools', "zh": '工具'},
    'menu.help': {"en": 'Help', "zh": '帮助'},
    'menu.import_documents': {"en": 'Import Documents...', "zh": '导入文档...'},
    'menu.export_xml': {"en": 'Export XML...', "zh": '导出 XML...'},
    'menu.import_xml': {"en": 'Import XML...', "zh": '导入 XML...'},
    'menu.settings': {"en": 'Settings', "zh": '设置'},
    'menu.extract': {"en": 'Extract Properties', "zh": '提取物性'},
    'menu.about': {"en": 'About', "zh": '关于'},
    'menu.exit': {"en": 'Exit', "zh": '退出'},
    'nav.toolbox': {"en": 'TOOLBOX', "zh": '工具箱'},
    'nav.materials': {"en": 'Materials', "zh": '材料库'},
    'nav.documents': {"en": 'Documents', "zh": '文档管理'},
    'nav.xml': {"en": 'XML Viewer', "zh": 'XML 查看器'},
    'nav.export': {"en": 'Export', "zh": '导出材料库'},
    'nav.settings': {"en": 'Settings', "zh": '设置'},
    'panel.browser': {"en": 'Material Browser', "zh": '材料浏览器'},
    'panel.editor': {"en": 'Property Editor', "zh": '属性编辑器'},
    'panel.chat': {"en": 'Q&A Chat', "zh": '智能问答'},
    'toolbar.main': {"en": 'Toolbar', "zh": '工具栏'},
    'toolbar.import': {"en": 'Import', "zh": '导入'},
    'toolbar.import_tip': {"en": 'Import supplier manuals', "zh": '导入供应商手册'},
    'toolbar.export': {"en": 'Export', "zh": '导出'},
    'toolbar.export_tip': {"en": 'Export to Ansys XML', "zh": '导出为 Ansys XML'},
    'toolbar.import_xml': {"en": 'Import XML', "zh": '查看XML材料库'},
    'toolbar.import_xml_tip': {"en": 'View Ansys XML file', "zh": '查看 Ansys XML 文件'},
    'toolbar.settings': {"en": 'Settings', "zh": '设置'},
    'toolbar.settings_tip': {"en": 'Open settings', "zh": '打开设置'},
    'toolbar.extract': {"en": 'Extract', "zh": '提取'},
    'toolbar.extract_tip': {"en": 'Extract material properties', "zh": '提取材料物性'},
    'status.materials': {"en": 'Materials: {count}', "zh": '材料: {count}'},
    'status.llm_not_configured': {"en": 'LLM: Not Configured', "zh": 'LLM: 未配置'},
    'editor.material_info': {"en": 'Material Information', "zh": '材料信息'},
    'editor.name': {"en": 'Name', "zh": '名称'},
    'editor.category': {"en": 'Category', "zh": '类别'},
    'editor.supplier': {"en": 'Supplier', "zh": '供应商'},
    'editor.product_name': {"en": 'Product Name', "zh": '产品名称'},
    'editor.save': {"en": 'Save Material', "zh": '保存材料'},
    'chat.not_configured': {"en": 'LLM not configured.', "zh": 'LLM未配置，请在设置中配置。'},
    'chat.header': {"en": 'AI Q&A', "zh": 'AI 问答'},
    'chat.placeholder': {"en": 'Ask about materials...', "zh": '询问材料知识...'},
    'chat.send': {"en": 'Send', "zh": '发送'},
    'chat.thinking': {"en": 'Thinking...', "zh": '思考中...'},
    'chat.clear_history': {"en": 'Clear History', "zh": '清除历史'},
    'docmgr.title': {"en": 'Document Manager', "zh": '文档管理'},
    'docmgr.btn_import': {"en": 'Import', "zh": '导入文档'},
    'docmgr.btn_extract': {"en": 'Extract', "zh": '提取物性'},
    'docmgr.btn_delete': {"en": 'Delete', "zh": '删除'},
    'docmgr.search_placeholder': {"en": 'Search...', "zh": '搜索文档...'},
    'docmgr.status_pending': {"en": 'Pending', "zh": '待处理'},
    'docmgr.status_completed': {"en": 'Completed', "zh": '已完成'},
    'docmgr.status_failed': {"en": 'Failed', "zh": '失败'},
    'docmgr.total_docs': {"en": 'Total: {count} documents', "zh": '共 {count} 个文档'},
    'docmgr.extract_done': {"en": 'Extracted {count} materials', "zh": '提取了 {count} 个材料'},
    'docmgr.extract_started': {"en": 'Extracting...', "zh": '提取中...'},
    'docmgr.confirm_delete': {"en": "Delete '{name}'?", "zh": "删除 '{name}'?"},
    'docmgr.parsing': {"en": 'Parsing...', "zh": '解析中...'},
    'docmgr.refresh': {"en": 'Refresh', "zh": '刷新'},
    'docmgr.col_filename': {"en": 'Filename', "zh": '文件名'},
    'docmgr.col_type': {"en": 'Type', "zh": '类型'},
    'docmgr.col_pages': {"en": 'Pages', "zh": '页数'},
    'docmgr.col_status': {"en": 'Status', "zh": '状态'},
    'docmgr.col_date': {"en": 'Date', "zh": '日期'},
    'docmgr.col_actions': {"en": 'Actions', "zh": '操作'},
    'browser.search_placeholder': {"en": 'Search materials...', "zh": '搜索材料...'},
    'browser.supplier': {"en": 'Supplier', "zh": '供应商'},
    'browser.all_suppliers': {"en": 'All Suppliers', "zh": '全部供应商'},
    'browser.find_duplicates': {"en": 'Find Duplicates', "zh": '查找重复'},
    'browser.no_duplicates': {"en": 'No duplicates found.', "zh": '未发现重复材料。'},
    'browser.dupes_found': {"en": 'Found {count} duplicate(s).', "zh": '发现 {count} 个重复。'},
    'browser.confirm_delete_dupes': {"en": 'Delete all duplicates except the first one?', "zh": '删除除第一条外的所有重复材料?'},
    'browser.edit': {"en": 'Edit', "zh": '编辑'},
    'browser.delete': {"en": 'Delete', "zh": '删除'},
    'browser.export_xml': {"en": 'Export XML', "zh": '导出XML'},
    'browser.delete_selected': {"en": 'Delete {count} selected material(s)?', "zh": '删除选中的 {count} 个材料?'},
    'browser.no_selection': {"en": 'No material selected.', "zh": '未选中材料。'},
    'prop.density': {"en": 'Density', "zh": '密度'},
    'prop.thermal_conductivity': {"en": 'Thermal Conductivity', "zh": '热导率'},
    'prop.specific_heat': {"en": 'Specific Heat', "zh": '比热容'},
    'prop.thermal_expansion': {"en": 'Thermal Expansion Coefficient', "zh": '热膨胀系数'},
    'prop.poisson_ratio': {"en": 'Poisson Ratio', "zh": '泊松比'},
    'prop.young_modulus': {"en": "Young's Modulus", "zh": '弹性模量'},
    'prop.tensile_strength': {"en": 'Tensile Strength', "zh": '抗拉强度'},
    'prop.yield_strength': {"en": 'Yield Strength', "zh": '屈服强度'},
    'prop.elastic_modulus': {"en": 'Elastic Modulus', "zh": '弹性模量'},
    'prop.melting_point': {"en": 'Melting Point', "zh": '熔点'},
    'prop.thermal_diffusivity': {"en": 'Thermal Diffusivity', "zh": '热扩散系数'},
    'prop_col.name': {"en": 'Property Name', "zh": '属性名称'},
    'prop_col.value': {"en": 'Value', "zh": '数值'},
    'prop_col.unit': {"en": 'Unit', "zh": '单位'},
    'prop_col.source': {"en": 'Source', "zh": '来源'},
    'prop_col.temp_dep': {"en": 'Temp Dependent', "zh": '温度依赖'},
    'prop_table.title': {"en": 'Material Properties', "zh": '材料属性'},
    'wiz.title': {"en": 'Import Documents', "zh": '导入文档'},
    'wiz.select_docs': {"en": 'Select Documents', "zh": '选择文档'},
    'wiz.select_hint': {"en": 'Choose PDF or image files.', "zh": '选择PDF或图片文件。'},
    'wiz.add_files': {"en": 'Add Files...', "zh": '添加文件...'},
    'wiz.remove_selected': {"en": 'Remove Selected', "zh": '移除选中'},
    'wiz.no_file': {"en": 'No file selected.', "zh": '未选择文件。'},
    'wiz.next': {"en": 'Next', "zh": '下一步'},
    'wiz.cancel': {"en": 'Cancel', "zh": '取消'},
    'wiz.back': {"en": 'Back', "zh": '上一步'},
    'wiz.finish': {"en": 'Finish', "zh": '完成'},
    'wiz.supplier': {"en": 'Supplier:', "zh": '供应商:'},
    'wiz.page_range': {"en": 'Page Range:', "zh": '页范围:'},
    'wiz.processing': {"en": 'Processing...', "zh": '处理中...'},
    'wiz.done': {"en": 'Done', "zh": '完成'},
    'wiz.result_file': {"en": 'File', "zh": '文件'},
    'wiz.result_status': {"en": 'Status', "zh": '状态'},
    'wiz.result_chunks': {"en": 'Chunks', "zh": '分块'},
    'wiz.options': {"en": 'Import Options', "zh": '导入选项'},
    'wiz.options_hint': {"en": 'Configure supplier and page range.', "zh": '配置供应商和页范围。'},
    'wiz.supplier_name': {"en": 'Supplier Name:', "zh": '供应商名称:'},
    'wiz.page_range_label': {"en": 'Page Range:', "zh": '页范围:'},
    'wiz.all_pages': {"en": 'All pages', "zh": '全部页'},
    'wiz.custom_range': {"en": 'Custom range:', "zh": '自定义范围:'},
    'wiz.from': {"en": 'From:', "zh": '从:'},
    'wiz.to': {"en": 'To:', "zh": '到:'},
    'wiz.notes': {"en": 'Notes:', "zh": '备注:'},
    'wiz.notes_hint': {"en": 'Optional notes...', "zh": '可选备注...'},
    'wiz.importing': {"en": 'Importing', "zh": '导入中'},
    'wiz.parsing_hint': {"en": 'Parsing files...', "zh": '解析中...'},
    'wiz.waiting': {"en": 'Waiting...', "zh": '等待中...'},
    'wiz.import_log': {"en": 'Import Log:', "zh": '导入日志:'},
    'wiz.starting_import': {"en": 'Starting {count} files...', "zh": '开始导入 {count} 个文件...'},
    'wiz.import_complete': {"en": 'Done: {done} ok, {fail} failed', "zh": '完成: {done} 成功, {fail} 失败'},
    'wiz.use_docmgr': {"en": 'Extract in Document Manager.', "zh": '请在文档管理中提取。'},
    'wiz.status_completed': {"en": 'Done:', "zh": '已完成:'},
    'wiz.status_skipped': {"en": 'Skipped:', "zh": '已跳过:'},
    'wiz.status_error': {"en": 'Error:', "zh": '错误:'},
    'wiz.finished_import': {"en": 'Finished {done}/{total}', "zh": '完成 {done}/{total}'},
    'wiz.summary': {"en": 'Import Summary', "zh": '导入摘要'},
    'wiz.summary_hint': {"en": 'Review results.', "zh": '查看结果。'},
    'wiz.no_results': {"en": 'No results.', "zh": '无结果。'},
    'wiz.files_processed': {"en": 'Processed', "zh": '已处理'},
    'wiz.successfully_imported': {"en": 'Imported', "zh": '已导入'},
    'wiz.skipped_dupes': {"en": 'Skipped', "zh": '已跳过'},
    'wiz.total_chunks': {"en": 'Chunks', "zh": '分块'},
    'wiz.doc_ids': {"en": 'IDs', "zh": 'ID'},
    'xml_import.title': {"en": 'XML Import', "zh": 'XML 导入'},
    'xml_import.file': {"en": 'File:', "zh": '文件:'},
    'xml_import.all_files': {"en": 'All Files', "zh": '所有文件'},
    'xml_import.materials': {"en": 'Materials', "zh": '材料列表'},
    'xml_import.detail': {"en": 'Detail', "zh": '详情'},
    'xml_import.materials_found': {"en": 'Materials Found:', "zh": '发现材料:'},
    'xml_import.open_file': {"en": 'Open File', "zh": '打开文件'},
    'xml_import.parse_error': {"en": 'Parse Error', "zh": '解析错误'},
    'xml_import.prop_name': {"en": 'Property Name', "zh": '属性名称'},
    'xml_import.value': {"en": 'Value', "zh": '数值'},
    'xml_import.unit': {"en": 'Unit', "zh": '单位'},
    'export.title': {"en": 'Export Material Library', "zh": '导出材料库'},
    'export.export_btn': {"en": 'Export to XML', "zh": '导出为 XML'},
    'export.format': {"en": 'Format:', "zh": '格式:'},
    'export.ansys_version': {"en": 'Ansys Version:', "zh": 'Ansys 版本:'},
    'export.select_materials': {"en": 'Select Materials:', "zh": '选择材料:'},
    'export.all': {"en": 'All', "zh": '全部'},
    'export.selected': {"en": 'Selected', "zh": '已选'},
    'export.output_path': {"en": 'Output Path:', "zh": '输出路径:'},
    'export.browse': {"en": 'Browse...', "zh": '浏览...'},
    'export.exporting': {"en": 'Exporting...', "zh": '导出中...'},
    'export.done': {"en": 'Export complete!', "zh": '导出完成!'},
    'export.error': {"en": 'Export failed', "zh": '导出失败'},
    'export.options': {"en": 'Export Options:', "zh": '导出选项:'},
    'export.single_file': {"en": 'Single File', "zh": '单文件'},
    'export.per_material': {"en": 'Per Material', "zh": '每材料一个文件'},
    'export.select_all': {"en": 'Select All', "zh": '全选'},
    'export.deselect_all': {"en": 'Deselect All', "zh": '取消全选'},
    'export.mat_name': {"en": 'Material Name', "zh": '材料名称'},
    'export.density': {"en": 'Density', "zh": '密度'},
    'export.thermal_cond': {"en": 'Thermal Conductivity', "zh": '热导率'},
    'export.specific_heat': {"en": 'Specific Heat', "zh": '比热容'},
    'export.status': {"en": 'Status', "zh": '状态'},
    'export.success': {"en": 'Complete', "zh": '完成'},
    'export.partial': {"en": 'Partial', "zh": '部分'},
    'export.failed': {"en": 'Failed', "zh": '失败'},
    'export.output_dir': {"en": 'Output Dir:', "zh": '输出目录:'},
    'export.select_dir': {"en": 'Select output directory...', "zh": '选择输出目录...'},
    'export.prefix': {"en": 'Prefix:', "zh": '文件前缀:'},
    'export.materials_count': {"en": '{count} material(s)', "zh": '{count} 个材料'},
    'export.no_materials': {"en": 'No materials in database.', "zh": '数据库中无材料。'},
    'export.no_output_dir': {"en": 'Please select output directory.', "zh": '请选择输出目录。'},
    'settings.title': {"en": 'Settings', "zh": '设置'},
    'settings.llm': {"en": 'LLM Configuration', "zh": '大模型配置'},
    'settings.llm_group': {"en": 'LLM Configuration', "zh": '大模型配置'},
    'settings.base_url': {"en": 'API Base URL:', "zh": 'API 基础地址:'},
    'settings.api_key': {"en": 'API Key:', "zh": 'API 密钥:'},
    'settings.model': {"en": 'Model:', "zh": '模型:'},
    'settings.temperature': {"en": 'Temperature:', "zh": '温度:'},
    'settings.max_tokens': {"en": 'Max Tokens:', "zh": '最大Token:'},
    'settings.test_connection': {"en": 'Test Connection', "zh": '测试连接'},
    'settings.test_success': {"en": 'Connection successful!', "zh": '连接成功!'},
    'settings.test_ok': {"en": 'Connection successful!', "zh": '连接成功!'},
    'settings.test_failed': {"en": 'Connection failed.', "zh": '连接失败。'},
    'settings.testing': {"en": 'Testing...', "zh": '测试中...'},
    'settings.language': {"en": 'Language:', "zh": '界面语言:'},
    'settings.save_settings': {"en": 'Save Settings', "zh": '保存设置'},
    'settings.settings_saved': {"en": 'Settings saved.', "zh": '设置已保存。'},
    'settings.embed_group': {"en": 'Embedding Configuration', "zh": '向量化配置'},
    'settings.embed_model': {"en": 'Embedding Model:', "zh": '向量模型:'},
    'settings.embed_backend': {"en": 'Backend:', "zh": '后端:'},
    'settings.ui_group': {"en": 'UI Settings', "zh": '界面设置'},
    'base_url': {"en": 'Base URL', "zh": '基础地址'},
    'api_key': {"en": 'API Key', "zh": 'API密钥'},
    'model': {"en": 'Model', "zh": '模型'},
    'temperature': {"en": 'Temperature', "zh": '温度'},
    'max_tokens': {"en": 'Max Tokens', "zh": '最大Token'},
    'language': {"en": 'Language', "zh": '语言'},
    'backend': {"en": 'Backend', "zh": '后端'},
    'unit': {"en": 'Unit', "zh": '单位'},
    'error': {"en": 'Error', "zh": '错误'},
    'status': {"en": 'Status', "zh": '状态'},
    'filename': {"en": 'Filename', "zh": '文件名'},
    'materials_found': {"en": 'Materials Found', "zh": '发现材料'},
    'chunk_count': {"en": 'Chunks', "zh": '分块'},
    'document_id': {"en": 'Document ID', "zh": '文档ID'},
    'ansys_materials': {"en": 'ansys_materials', "zh": 'ansys_materials'},
    'Thinking': {"en": 'Thinking...', "zh": '思考中...'}
}
class Translator:
    def __init__(self, database=None):
        self._db = database
        self._lang = "zh"
        if database:
            raw = database.get_setting("ui.language")
            if raw and raw in SUPPORTED_LANGUAGES:
                self._lang = raw

    @property
    def language(self):
        return self._lang

    @language.setter
    def language(self, lang):
        if lang in SUPPORTED_LANGUAGES:
            self._lang = lang
            if self._db:
                self._db.set_setting("ui.language", lang)

    def t(self, key, **kwargs):
        entry = _TRANSLATIONS.get(key, {})
        text = entry.get(self._lang) or entry.get("en") or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    def set_language(self, lang):
        self.language = lang

_translator = None

def init_translator(database=None):
    global _translator
    _translator = Translator(database)
    return _translator

def get_translator():
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator

def t(key, **kwargs):
    return get_translator().t(key, **kwargs)

def pt(name):
    """Translate a property name."""
    return get_translator().t("prop." + name)
