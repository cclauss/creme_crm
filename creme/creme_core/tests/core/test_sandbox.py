# -*- coding: utf-8 -*-

try:
    from ..base import CremeTestCase

    from creme.creme_core.core.sandbox import (SandboxType,
            _SandboxTypeRegistry, sandbox_type_registry)
    from creme.creme_core.models import Sandbox
except Exception as e:
    print(f'Error in <{__name__}>: {e}')


class SandboxTestCase(CremeTestCase):
    def test_registry01(self):
        name = 'Test sandbox #1'

        class TestSandboxType1(SandboxType):
            id = SandboxType.generate_id('creme_core', 'test1')
            verbose_name = name

        sandbox_type_registry.register(TestSandboxType1)  # TODO: unregister in tearDown ?

        sandbox = Sandbox(type_id=TestSandboxType1.id)

        st_type = sandbox.type
        self.assertIsInstance(st_type, TestSandboxType1)
        self.assertEqual(name, st_type.verbose_name)

    def test_registry02(self):
        registry = _SandboxTypeRegistry()

        st_id = SandboxType.generate_id('creme_core', 'test2')

        class TestSandboxType2_2(SandboxType):
            id = st_id
            verbose_name = 'Test sandbox #2'

        class TestSandboxType2_3(SandboxType):
            id = st_id
            verbose_name = 'Test sandbox #3'

        registry.register(TestSandboxType2_2)

        with self.assertRaises(_SandboxTypeRegistry.Error):
            registry.register(TestSandboxType2_3)

        sandbox1 = Sandbox(type_id=TestSandboxType2_2.id)
        self.assertIsInstance(registry.get(sandbox1), TestSandboxType2_2)

        class TestSandboxType2_4(SandboxType):  # Not registered
            id = SandboxType.generate_id('creme_core', 'unknown')
            verbose_name = 'Test sandbox #4'

        sandbox2 = Sandbox(type_id=TestSandboxType2_4.id)

        with self.assertLogs(level='CRITICAL') as logs_manager:
            sb_type = registry.get(sandbox2)

        self.assertIsNone(sb_type)
        self.assertEqual(
            logs_manager.output,
            [f'CRITICAL:creme.creme_core.core.sandbox:Unknown SandboxType: {TestSandboxType2_4.id}'],
        )

    def test_sandbox_data(self):
        user = self.login()
        fmt = 'Restricted to "{}"'

        class TestSandboxType3(SandboxType):
            id = SandboxType.generate_id('creme_core', 'test3')

            @property
            def verbose_name(self):
                return fmt.format(self.sandbox.user)

        sandbox_type_registry.register(TestSandboxType3)  # TODO: unregister in tearDown ?

        sandbox = Sandbox(type_id=TestSandboxType3.id, user=user)
        self.assertEqual(fmt.format(user), sandbox.type.verbose_name)
