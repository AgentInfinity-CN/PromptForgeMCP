#!/usr/bin/env python3
"""
PromptForge MCP Client 测试脚本
============================

用于测试PromptForge MCP服务的各项功能
"""

import asyncio
import json
from fastmcp import Client

async def test_promptforge_mcp():
    """测试PromptForge MCP服务的主要功能"""
    
    # 连接到本地MCP服务器
    # 注意：需要先启动 python -m promptforge_mcp.main --http
    # 端口号根据 .env 中的 MCP_SERVER_PORT 配置，默认为 8080
    client = Client("http://localhost:8080")
    
    try:
        async with client:
            print("🔗 已连接到PromptForge MCP服务器")
            
            # 1. 测试获取服务器配置
            print("\n📋 测试服务器配置...")
            config = await client.read_resource("promptforge://config")
            print(f"✅ 服务器配置: {config[0].text[:200]}...")
            
            # 2. 测试获取服务器状态  
            print("\n💓 测试服务器状态...")
            status = await client.read_resource("promptforge://status")
            print(f"✅ 服务器状态: {status[0].text}")
            
            # 3. 测试提示分析
            print("\n🔍 测试提示分析...")
            test_prompt = "请总结以下文本的主要观点并提供深入的见解分析。"
            
            analysis_result = await client.call_tool("analyze_prompt", {
                "prompt": test_prompt,
                "analysis_type": "dual"  # 使用配置默认模型
            })
            
            if analysis_result.data and analysis_result.data.get('success'):
                print("✅ 提示分析成功")
                print(f"   📊 指标: {analysis_result.data['metrics']}")
                print(f"   💡 建议数量: {len(analysis_result.data['suggestions'])}")
            else:
                print("❌ 提示分析失败")
            
            # 4. 测试提示执行
            print("\n⚡ 测试提示执行...")
            execution_result = await client.call_tool("execute_prompt", {
                "prompt": "你好，我的名字是{name}，请介绍一下{topic}",
                "variables": {"name": "测试用户", "topic": "人工智能"},
                "temperature": 0.7,
                "max_tokens": 500
            })
            
            if execution_result.data and execution_result.data.get('success'):
                print("✅ 提示执行成功")
                print(f"   ⏱️ 执行时间: {execution_result.data['execution_time']:.2f}秒")
                print(f"   📝 响应长度: {len(execution_result.data['response'])}字符")
            else:
                print("❌ 提示执行失败")
            
            # 5. 测试保存提示
            print("\n💾 测试保存提示...")
            save_result = await client.call_tool("save_prompt", {
                "title": "测试提示",
                "content": "这是一个用于测试的提示内容：{variable}",
                "description": "测试用的提示模板",
                "category": "Test",
                "tags": ["test", "demo", "template"]
            })
            
            if save_result.data and save_result.data.get('id'):
                prompt_id = save_result.data['id']
                print(f"✅ 提示保存成功，ID: {prompt_id}")
                
                # 7. 测试获取提示
                print("\n📖 测试获取提示...")
                get_result = await client.call_tool("get_saved_prompt", {
                    "prompt_id": prompt_id
                })
                
                if get_result.data:
                    print("✅ 提示获取成功")
                    print(f"   📝 标题: {get_result.data['title']}")
                else:
                    print("❌ 提示获取失败")
                
                # 8. 测试搜索提示
                print("\n🔍 测试搜索提示...")
                search_result = await client.call_tool("search_prompts", {
                    "query": "测试",
                    "category": "Test",
                    "tags": ["test"],
                    "limit": 10
                })
                
                if search_result.data:
                    print(f"✅ 搜索成功，找到 {len(search_result.data)} 个结果")
                else:
                    print("❌ 搜索失败")
                
                # 9. 测试删除提示
                print("\n🗑️ 测试删除提示...")
                delete_result = await client.call_tool("delete_prompt", {
                    "prompt_id": prompt_id
                })
                
                if delete_result.data and delete_result.data.get('success'):
                    print("✅ 提示删除成功")
                else:
                    print("❌ 提示删除失败")
            else:
                print("❌ 提示保存失败")
            
            # 8. 测试获取历史记录
            print("\n📈 测试获取历史记录...")
            history = await client.read_resource("promptforge://history/5")
            print(f"✅ 历史记录: {len(json.loads(history[0].text))} 条")
            
            print("\n🎉 所有测试完成！")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        print("💡 请确保 PromptForge MCP 服务器正在运行:")
        print("   uv run promptforge_mcp_server.py --http --port 8000")

async def test_tools_list():
    """测试获取可用工具列表"""
    client = Client("http://localhost:8000")
    
    try:
        async with client:
            print("\n🛠️ 可用工具列表:")
            tools = await client.list_tools()
            
            for tool in tools:
                print(f"   📋 {tool.name}: {tool.description}")
                
            print(f"\n📊 总计 {len(tools)} 个工具")
            
    except Exception as e:
        print(f"❌ 获取工具列表失败: {e}")

async def test_resources_list():
    """测试获取可用资源列表"""
    client = Client("http://localhost:8000")
    
    try:
        async with client:
            print("\n📁 可用资源列表:")
            resources = await client.list_resources()
            
            for resource in resources:
                print(f"   📄 {resource.uri}: {resource.name}")
                
            print(f"\n📊 总计 {len(resources)} 个资源")
            
    except Exception as e:
        print(f"❌ 获取资源列表失败: {e}")

async def main():
    """主函数"""
    print("🧪 PromptForge MCP 服务测试")
    print("=" * 50)
    
    # 测试工具和资源列表
    await test_tools_list()
    await test_resources_list()
    
    # 运行完整功能测试
    await test_promptforge_mcp()

if __name__ == "__main__":
    asyncio.run(main()) 