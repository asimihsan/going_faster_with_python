# -------------------------------------------------------------------
#   Hack distutils to stop being a muppet and throwing
#   -Qunused-arguments around. Needed to get gcc-4.7 working.
# -------------------------------------------------------------------
import distutils
import distutils.sysconfig
distutils.sysconfig.get_config_vars()
for key in distutils.sysconfig._config_vars:
    if key in ['CONFIG_ARGS', 'PY_CFLAGS', 'CFLAGS']:
        distutils.sysconfig._config_vars[key] = distutils.sysconfig._config_vars[key].replace("-Qunused-arguments ", "")
# -------------------------------------------------------------------

# PCRE reference: http://www.mitchr.me/SS/exampleCode/AUPG/pcre_example.c.html

from cffi import FFI

def _make_ffi_process_line():
    libraries = ['c', 'pcre']
    extra_compile_args = []
    extra_link_args = []
    #extra_compile_args = ['-fprofile-generate']
    #extra_link_args = ['-fprofile-generate']
    #extra_compile_args = ['-fprofile-use']
    #extra_link_args = ['-fprofile-use']

    ffi = FFI()

    ffi.cdef(r"""
    int process_line(const char* line);
    """)

    lib = ffi.verify(r"""
    #include "pcre.h"

    static char* regex = "(.*?),(.*?),(.*)";
    static pcre* re;
    static pcre_extra* extra;

    pcre* compile_regexp(char* regexp) {
        const char* error;
        int erroffset;
        re = pcre_compile(regex,
                          PCRE_UTF8,
                          &error,
                          &erroffset,
                          0);
        if (!re) {
            printf("pcre_compile failed (offset: %d), %s\n", erroffset, error);
        }
        return re;
    }

    pcre_extra* study_regexp(pcre* compiled_regexp) {
        const char* error;
        extra = pcre_study(re, PCRE_STUDY_JIT_COMPILE, &error);
        if (error != NULL) {
            printf("pcre_study failed: '%s'\n", error);
        }
        return extra;
    }

    int process_line(const char* line) {
        int rc, i;
        const int MAX_OFFSETS = 30;
        const char* value;
        const char* metric;
        static char* cpu_usage = "cpu_usage";
        int metric_len;
        if (!re) {
            re = compile_regexp(regex);
            extra = study_regexp(re);
        }
        int offsets[MAX_OFFSETS];
        rc = pcre_exec(re, extra, line, strlen(line), 0, 0, offsets, MAX_OFFSETS);
        if (rc < 0) {
            if (rc == PCRE_ERROR_NOMATCH) printf("Did not match\n");
            else printf("Matching error %d\n", rc);
            return -1;
        }
        pcre_get_substring(line, offsets, rc, 2, &(metric));
        metric_len = offsets[2*2+1] - offsets[2*2];
        if (!strncmp(metric, cpu_usage, metric_len)) {
            pcre_get_substring(line, offsets, rc, 3, &(value));
            return atoi(value);
        }
        return -1;
    };
    """, libraries=libraries,
         extra_compile_args=extra_compile_args,
         extra_link_args=extra_link_args)

    return lib.process_line

