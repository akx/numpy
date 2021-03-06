import sys, platform, re, pytest

from numpy.testing import assert_equal
from numpy.core._multiarray_umath import __cpu_features__

class AbstractTest(object):
    features = []
    features_groups = {}
    features_map = {}
    features_flags = set()

    def load_flags(self):
        # a hook
        pass

    def test_features(self):
        self.load_flags()
        for gname, features in self.features_groups.items():
            test_features = [self.features_map.get(f, f) in self.features_flags for f in features]
            assert_equal(__cpu_features__.get(gname), all(test_features))

        for feature_name in self.features:
            map_name = self.features_map.get(feature_name, feature_name)
            cpu_have = map_name in self.features_flags
            npy_have = __cpu_features__.get(feature_name)
            assert_equal(npy_have, cpu_have)

    def load_flags_proc(self, magic_key):
        with open('/proc/cpuinfo') as fd:
            for line in fd:
                if not line.startswith(magic_key):
                    continue
                flags_value = [s.strip() for s in line.split(':', 1)]
                if len(flags_value) == 2:
                    self.features_flags = self.features_flags.union(flags_value[1].upper().split())

    def load_flags_auxv(self):
        import subprocess
        auxv = subprocess.check_output(['/bin/true'], env=dict(LD_SHOW_AUXV="1"))
        for at in auxv.split(b'\n'):
            if not at.startswith(b"AT_HWCAP"):
                continue
            hwcap_value = [s.strip() for s in at.split(b':', 1)]
            if len(hwcap_value) == 2:
                self.features_flags = self.features_flags.union(
                    hwcap_value[1].upper().decode().split()
                )

is_linux = sys.platform.startswith('linux')
machine  = platform.machine()
is_x86   = re.match("^(amd64|x86|i386|i686)", machine, re.IGNORECASE)
@pytest.mark.skipif(not is_linux or not is_x86, reason="Only for Linux and x86")
class Test_X86_Features(AbstractTest):
    features = [
        "MMX", "SSE", "SSE2", "SSE3", "SSSE3", "SSE41", "POPCNT", "SSE42",
        "AVX", "F16C", "XOP", "FMA4", "FMA3", "AVX2", "AVX512F", "AVX512CD",
        "AVX512ER", "AVX512PF", "AVX5124FMAPS", "AVX5124VNNIW", "AVX512VPOPCNTDQ",
        "AVX512VL", "AVX512BW", "AVX512DQ", "AVX512VNNI", "AVX512IFMA",
        "AVX512VBMI", "AVX512VBMI2", "AVX512BITALG",
    ]
    features_groups = dict(
        AVX512_KNL = ["AVX512F", "AVX512CD", "AVX512ER", "AVX512PF"],
        AVX512_KNM = ["AVX512F", "AVX512CD", "AVX512ER", "AVX512PF", "AVX5124FMAPS",
                      "AVX5124VNNIW", "AVX512VPOPCNTDQ"],
        AVX512_SKX = ["AVX512F", "AVX512CD", "AVX512BW", "AVX512DQ", "AVX512VL"],
        AVX512_CLX = ["AVX512F", "AVX512CD", "AVX512BW", "AVX512DQ", "AVX512VL", "AVX512VNNI"],
        AVX512_CNL = ["AVX512F", "AVX512CD", "AVX512BW", "AVX512DQ", "AVX512VL", "AVX512IFMA",
                      "AVX512VBMI"],
        AVX512_ICL = ["AVX512F", "AVX512CD", "AVX512BW", "AVX512DQ", "AVX512VL", "AVX512IFMA",
                      "AVX512VBMI", "AVX512VNNI", "AVX512VBMI2", "AVX512BITALG", "AVX512VPOPCNTDQ"],
    )
    features_map = dict(
        SSE3="PNI", SSE41="SSE4_1", SSE42="SSE4_2", FMA3="FMA",
        AVX512VNNI="AVX512_VNNI", AVX512BITALG="AVX512_BITALG", AVX512VBMI2="AVX512_VBMI2",
        AVX5124FMAPS="AVX512_4FMAPS", AVX5124VNNIW="AVX512_4VNNIW", AVX512VPOPCNTDQ="AVX512_VPOPCNTDQ",
    )
    def load_flags(self):
        self.load_flags_proc("flags")

is_power = re.match("^(powerpc|ppc)64", machine, re.IGNORECASE)
@pytest.mark.skipif(not is_linux or not is_power, reason="Only for Linux and Power")
class Test_POWER_Features(AbstractTest):
    features = ["VSX", "VSX2", "VSX3"]
    features_map = dict(VSX2="ARCH_2_07", VSX3="ARCH_3_00")

    def load_flags(self):
        self.load_flags_auxv()

is_arm = re.match("^(arm|aarch64)", machine, re.IGNORECASE)
@pytest.mark.skipif(not is_linux or not is_arm, reason="Only for Linux and ARM")
class Test_ARM_Features(AbstractTest):
    features = [
        "NEON", "ASIMD", "FPHP", "ASIMDHP", "ASIMDDP", "ASIMDFHM"
    ]
    features_groups = dict(
        NEON_FP16  = ["NEON", "HALF"],
        NEON_VFPV4 = ["NEON", "VFPV4"],
    )
    def load_flags(self):
        self.load_flags_proc("Features")
        if re.match("^(aarch64|AARCH64)", platform.machine()):
            self.features_map = dict(
                NEON="ASIMD", HALF="ASIMD", VFPV4="ASIMD"
            )
