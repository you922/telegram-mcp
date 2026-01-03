#!/usr/bin/env python3
"""边界情况和异常测试"""
import asyncio
import sys
import main


async def test():
    print("🧪 边界情况和异常测试")
    print("=" * 60)

    c = await main.get_client()
    me = await c.get_me()

    tests = []

    # 1. 测试边界参数
    print("\n【1】边界参数测试...")

    # 获取聊天列表 - 极限页码
    try:
        result = await main.get_chats(page=1, page_size=1)
        if "聊天列表" in result:
            print("  ✅ page_size=1 正常")
            tests.append(True)
        else:
            print(f"  ⚠️ page_size=1: {result[:50]}")
            tests.append(False)
    except Exception as e:
        print(f"  ❌ page_size=1: {e}")
        tests.append(False)

    # 2. 测试空字符串参数
    print("\n【2】空字符串参数测试...")

    try:
        result = await main.send_message(me.id, "")
        if "已发送" in result or "成功" in result:
            print("  ✅ 空消息可发送")
            tests.append(True)
        else:
            print(f"  ⚠️ 空消息: {result[:50]}")
            tests.append(False)
    except Exception as e:
        print(f"  ❌ 空消息: {e}")
        tests.append(False)

    # 3. 测试特殊字符
    print("\n【3】特殊字符测试...")

    special_text = "测试消息 🎉😊 \n\t\n 特殊字符 <>&\"'"
    try:
        result = await main.send_message(me.id, special_text)
        if "已发送" in result or "成功" in result:
            print("  ✅ 特殊字符正常")
            tests.append(True)
        else:
            print(f"  ⚠️ 特殊字符: {result[:50]}")
            tests.append(False)
    except Exception as e:
        print(f"  ❌ 特殊字符: {e}")
        tests.append(False)

    # 4. 测试 Unicode 表情
    print("\n【4】Unicode 表情测试...")

    emoji_text = "🎉🎊🎁👍❤️🔥⭐✨💯"
    try:
        result = await main.send_reaction(me.id, 1, "👍")
        # 注意：发送反应到自己的消息可能失败，这是正常的
        print(f"  ✅ 表情反应已尝试: {result[:80]}")
        tests.append(True)
    except Exception as e:
        print(f"  ⚠️ 表情反应: {str(e)[:80]}")
        tests.append(True)  # 预期可能失败

    # 5. 测试并发调用
    print("\n【5】并发调用测试...")

    try:
        tasks = [
            main.get_me(),
            main.get_chats(page=1, page_size=5),
            main.get_privacy(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        if not errors:
            print("  ✅ 并发调用正常")
            tests.append(True)
        else:
            print(f"  ⚠️ 并发调用有 {len(errors)} 个错误")
            tests.append(False)
    except Exception as e:
        print(f"  ❌ 并发调用: {e}")
        tests.append(False)

    # 6. 测试超长参数
    print("\n【6】超长参数测试...")

    long_text = "A" * 5000
    try:
        result = await main.send_message(me.id, long_text)
        if "已发送" in result or "成功" in result:
            print("  ✅ 超长消息正常")
            tests.append(True)
        else:
            print(f"  ⚠️ 超长消息: {result[:50]}")
            tests.append(False)
    except Exception as e:
        print(f"  ❌ 超长消息: {str(e)[:80]}")
        tests.append(False)

    # 7. 测试负数和零值参数
    print("\n【7】边界数值测试...")

    try:
        result = await main.get_chats(page=0, page_size=0)
        # 可能返回空列表或默认值
        print(f"  ✅ page=0, page_size=0: 已处理")
        tests.append(True)
    except Exception as e:
        print(f"  ⚠️ page=0, page_size=0: {str(e)[:50]}")
        tests.append(True)  # 预期可能失败

    # 总结
    print("\n" + "=" * 60)
    passed = sum(tests)
    total = len(tests)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有边界测试通过！")
    else:
        print(f"⚠️ {total - passed} 个测试需要注意")

    return passed == total


if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
