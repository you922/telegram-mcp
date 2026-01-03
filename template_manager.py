#!/usr/bin/env python3
"""
消息模板管理模块
AI 可以调用预设模板发送消息
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import re


ACCOUNTS_DIR = "./accounts"
TEMPLATE_FILE = os.path.join(ACCOUNTS_DIR, "templates.json")


class TemplateManager:
    """消息模板管理器"""

    def __init__(self):
        self.templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self):
        """加载模板"""
        if os.path.exists(TEMPLATE_FILE):
            try:
                with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates = data.get("templates", {})
            except:
                self.templates = {}

    def _save_templates(self):
        """保存模板"""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "templates": self.templates,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

    def add_template(
        self,
        template_id: str,
        name: str,
        content: str,
        category: str = "其他",
        variables: List[str] = None
    ) -> bool:
        """
        添加模板

        Args:
            template_id: 模板ID
            name: 模板名称
            content: 模板内容
            category: 分类
            variables: 变量列表

        Returns:
            是否成功
        """
        # 自动提取变量 {name}, {time} 等
        if variables is None:
            variables = re.findall(r'\{(\w+)\}', content)

        self.templates[template_id] = {
            "id": template_id,
            "template_id": template_id,  # 前端使用的字段名
            "name": name,
            "content": content,
            "category": category,
            "variables": variables,
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }

        self._save_templates()
        return True

    def get_template(self, template_id: str) -> Optional[Dict]:
        """获取模板"""
        template = self.templates.get(template_id)
        if template and "template_id" not in template:
            # 确保 template_id 字段存在（兼容旧数据）
            template = dict(template)
            template["template_id"] = template.get("id")
        return template

    def list_templates(self, category: str = None) -> List[Dict]:
        """
        列出模板

        Args:
            category: 筛选分类

        Returns:
            模板列表
        """
        templates = []
        for t in self.templates.values():
            # 确保 template_id 字段存在（兼容旧数据）
            template = dict(t)
            if "template_id" not in template and "id" in template:
                template["template_id"] = template["id"]
            templates.append(template)

        if category:
            templates = [t for t in templates if t.get("category") == category]

        # 按使用次数排序
        templates.sort(key=lambda x: x.get("use_count", 0), reverse=True)

        return templates

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功
        """
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_templates()
            return True
        return False

    def render_template(self, template_id: str, **kwargs) -> Optional[str]:
        """
        渲染模板（替换变量）

        Args:
            template_id: 模板ID
            **kwargs: 变量值

        Returns:
            渲染后的内容
        """
        template = self.get_template(template_id)
        if not template:
            return None

        content = template["content"]

        # 替换变量
        for var in template.get("variables", []):
            placeholder = "{" + var + "}"
            value = kwargs.get(var, "")
            content = content.replace(placeholder, str(value))

        # 更新使用次数
        template["use_count"] = template.get("use_count", 0) + 1
        template["last_used"] = datetime.now().isoformat()
        self._save_templates()

        return content

    def update_template(
        self,
        template_id: str,
        name: str = None,
        content: str = None,
        category: str = None
    ) -> bool:
        """
        更新模板

        Args:
            template_id: 模板ID
            name: 新名称
            content: 新内容
            category: 新分类

        Returns:
            是否成功
        """
        if template_id not in self.templates:
            return False

        template = self.templates[template_id]

        if name:
            template["name"] = name
        if content:
            template["content"] = content
            # 重新提取变量
            template["variables"] = re.findall(r'\{(\w+)\}', content)
        if category:
            template["category"] = category

        template["updated_at"] = datetime.now().isoformat()
        self._save_templates()
        return True

    def search_templates(self, keyword: str) -> List[Dict]:
        """
        搜索模板

        Args:
            keyword: 关键词

        Returns:
            匹配的模板列表
        """
        keyword_lower = keyword.lower()
        return [
            t for t in self.templates.values()
            if keyword_lower in t.get("name", "").lower()
            or keyword_lower in t.get("content", "").lower()
            or keyword_lower in t.get("category", "").lower()
        ]

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set(t.get("category", "其他") for t in self.templates.values())
        return sorted(categories)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total": len(self.templates),
            "by_category": {
                cat: len([t for t in self.templates.values() if t.get("category") == cat])
                for cat in self.get_categories()
            },
            "most_used": sorted(
                self.templates.values(),
                key=lambda x: x.get("use_count", 0),
                reverse=True
            )[:5],
            "recently_created": sorted(
                self.templates.values(),
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:5]
        }


# 全局实例
template_manager = TemplateManager()
