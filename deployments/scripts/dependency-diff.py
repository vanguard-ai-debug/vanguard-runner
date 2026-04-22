#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量依赖安装脚本
- 比较requirements.txt和requirements-lock.txt
- 只安装新增、修改或删除的依赖
- 支持版本升级检测
"""
import os
import re
import subprocess
import sys
from pathlib import Path


class DependencyDiff:
    def __init__(self):
        self.requirements_file = "requirements.txt"
        self.lock_file = "requirements-lock.txt"
        self.work_dir = Path("/app")
    
    def parse_requirements(self, file_path):
        """解析requirements文件，返回包名和版本的字典"""
        requirements = {}
        
        if not file_path.exists():
            return requirements
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析包名和版本
                match = re.match(r'^([a-zA-Z0-9_-]+[a-zA-Z0-9_.-]*)', line)
                if match:
                    package_name = match.group(1).lower()
                    # 提取版本号
                    version_match = re.search(r'==([0-9.]+)', line)
                    version = version_match.group(1) if version_match else None
                    requirements[package_name] = {
                        'version': version,
                        'full_line': line
                    }
        
        return requirements
    
    def get_current_installed(self):
        """获取当前已安装的包"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                                  capture_output=True, text=True, check=True)
            installed = {}
            
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    package, version = line.split('==', 1)
                    installed[package.lower()] = version
            
            return installed
        except subprocess.CalledProcessError as e:
            print(f"❌ 获取已安装包失败: {e}")
            return {}
    
    def compare_dependencies(self):
        """比较依赖差异"""
        current_req = self.parse_requirements(self.work_dir / self.requirements_file)
        locked_req = self.parse_requirements(self.work_dir / self.lock_file)
        installed_packages = self.get_current_installed()
        
        # 分析差异
        to_install = []      # 需要安装的新包
        to_upgrade = []      # 需要升级的包
        to_downgrade = []    # 需要降级的包
        to_remove = []       # 需要移除的包
        
        # 检查新增和修改的包
        for package, info in current_req.items():
            if package not in locked_req:
                # 新包
                to_install.append(info['full_line'])
                print(f"🆕 新增依赖: {package}")
            elif package in locked_req:
                current_version = info.get('version')
                locked_version = locked_req[package].get('version')
                
                if current_version and locked_version and current_version != locked_version:
                    # 版本变化
                    if self.compare_versions(current_version, locked_version) > 0:
                        to_upgrade.append(info['full_line'])
                        print(f"⬆️ 升级依赖: {package} {locked_version} -> {current_version}")
                    else:
                        to_downgrade.append(info['full_line'])
                        print(f"⬇️ 降级依赖: {package} {locked_version} -> {current_version}")
        
        # 检查需要移除的包
        for package, info in locked_req.items():
            if package not in current_req:
                to_remove.append(package)
                print(f"🗑️ 移除依赖: {package}")
        
        return {
            'to_install': to_install,
            'to_upgrade': to_upgrade,
            'to_downgrade': to_downgrade,
            'to_remove': to_remove
        }
    
    def compare_versions(self, version1, version2):
        """比较版本号，返回1表示version1>version2，-1表示version1<version2，0表示相等"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        try:
            v1 = version_tuple(version1)
            v2 = version_tuple(version2)
            
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
            else:
                return 0
        except ValueError:
            # 版本格式不标准，按字符串比较
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            else:
                return 0
    
    def install_packages(self, packages, operation="install"):
        """安装或升级包"""
        if not packages:
            return True
        
        print(f"📦 {operation} {len(packages)} 个包...")
        
        for package in packages:
            try:
                if operation == "install":
                    cmd = [sys.executable, '-m', 'pip', 'install', package]
                elif operation == "upgrade":
                    cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', package]
                else:
                    continue
                
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ {operation}: {package}")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ {operation}失败: {package}")
                print(f"错误信息: {e.stderr}")
                return False
        
        return True
    
    def remove_packages(self, packages):
        """移除包"""
        if not packages:
            return True
        
        print(f"🗑️ 移除 {len(packages)} 个包...")
        
        for package in packages:
            try:
                cmd = [sys.executable, '-m', 'pip', 'uninstall', '-y', package]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ 移除: {package}")
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️ 移除失败: {package} (可能不存在)")
        
        return True
    
    def update_lock_file(self):
        """更新锁定文件"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                                  capture_output=True, text=True, check=True)
            
            with open(self.work_dir / self.lock_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            print("📝 更新锁定文件完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 更新锁定文件失败: {e}")
            return False
    
    def install_incremental(self):
        """执行增量安装"""
        print("🔍 分析依赖差异...")
        
        # 比较依赖
        diff = self.compare_dependencies()
        
        total_changes = (len(diff['to_install']) + len(diff['to_upgrade']) + 
                        len(diff['to_downgrade']) + len(diff['to_remove']))
        
        if total_changes == 0:
            print("✅ 没有依赖变化，跳过安装")
            return True
        
        print(f"📊 发现 {total_changes} 个依赖变化")
        
        # 执行操作
        success = True
        
        # 移除不需要的包
        if not self.remove_packages(diff['to_remove']):
            success = False
        
        # 降级包
        if not self.install_packages(diff['to_downgrade'], "install"):
            success = False
        
        # 升级包
        if not self.install_packages(diff['to_upgrade'], "upgrade"):
            success = False
        
        # 安装新包
        if not self.install_packages(diff['to_install'], "install"):
            success = False
        
        # 更新锁定文件
        if success:
            self.update_lock_file()
        
        return success


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        diff_manager = DependencyDiff()
        success = diff_manager.install_incremental()
        sys.exit(0 if success else 1)
    else:
        print("用法: python dependency-diff.py install")
        sys.exit(1)


if __name__ == "__main__":
    main()
