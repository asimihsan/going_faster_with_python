# -----------------------------------------------------------------------------
# !!AI TODO
# - I'm being very naughty; there's a whole bunch of C free'ing that
#   I'm ignoring. But this is out of the scope of the presentation.
#   For reference refer to the "JIT reference" for an example.
#
#   pcre_free(re);
#   pcre_free_study(extra);
#   pcre_jit_stack_free(jit_stack);
# -----------------------------------------------------------------------------

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
# PCRE JIT reference: http://www.manpagez.com/man/3/pcrejit/
# PCRE man page: http://vcs.pcre.org/viewvc/code/trunk/doc/pcre.txt?view=markup

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
    static pcre_jit_stack *jit_stack;

    pcre* compile_regexp(char* regexp) {
        const char* error;
        int erroffset;
        re = pcre_compile(regex,
                          0, // PCRE_UTF8,
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
        jit_stack = pcre_jit_stack_alloc(32*1024, 512*1024);
        pcre_assign_jit_stack(extra, NULL, jit_stack);
        return extra;
    }

    int process_line(const char* line) {
        int rc, i;

        /* see man page section 'How pcre_exec() returns captured */
        /* substrings'                                            */
        const int MAX_CAPTURE_GROUPS = 10;
        const int MAX_OFFSETS = MAX_CAPTURE_GROUPS * 3;
        int offsets[MAX_OFFSETS];
        const char* metric;
        int metric_len;
        const int METRIC_MATCH_GROUP_NUMBER = 1;
        const int METRIC_OFFSET_START = (METRIC_MATCH_GROUP_NUMBER + 1) * 2;
        const int METRIC_OFFSET_END = (METRIC_MATCH_GROUP_NUMBER + 1) * 2 + 1;
        static char* cpu_usage = "cpu_usage";
        const char* value;
        const int VALUE_MATCH_GROUP_NUMBER = 2;

        if (!re) {
            re = compile_regexp(regex);
            extra = study_regexp(re);
        }
        rc = pcre_jit_exec(re,           /* result of pcre_compile() */
                           extra,        /* result of pcre_study() */
                           line,         /* the subject string */
                           strlen(line), /* length of subject string */
                           0,            /* start at offset 0 in the subject */
                           0,            /* default options */
                           offsets,      /* vector of integers for substring info */
                           MAX_OFFSETS,  /* number of elements */
                           jit_stack);   /* result of pcre_jit_stack_alloc() */
        if (rc < 0) {
            if (rc == PCRE_ERROR_NOMATCH) printf("Did not match\n");
            else printf("Matching error %d\n", rc);
            return -1;
        }
        pcre_get_substring(line,
                           offsets,
                           rc,
                           METRIC_MATCH_GROUP_NUMBER + 1,
                           &(metric));
        metric_len = offsets[METRIC_OFFSET_END] - offsets[METRIC_OFFSET_START];
        if (!strncmp(metric, cpu_usage, metric_len)) {
            pcre_get_substring(line,
                               offsets,
                               rc,
                               VALUE_MATCH_GROUP_NUMBER + 1,
                               &(value));
            return atoi(value);
        }
        return -1;
    };
    """, libraries=libraries,
         extra_compile_args=extra_compile_args,
         extra_link_args=extra_link_args)

    return lib.process_line

