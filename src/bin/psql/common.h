/*
 * psql - the PostgreSQL interactive terminal
 *
 * Copyright (c) 2000-2010, PostgreSQL Global Development Group
 *
 * $PostgreSQL: pgsql/src/bin/psql/common.h,v 1.54 2007/01/05 22:19:49 momjian Exp $
 */
#ifndef COMMON_H
#define COMMON_H

#include "postgres_fe.h"
#include <setjmp.h>
#include "libpq-fe.h"

#ifdef USE_ASSERT_CHECKING
#include <assert.h>
#define psql_assert(p) assert(p)
#else
#define psql_assert(p)
#endif

#define atooid(x)  ((Oid) strtoul((x), NULL, 10))

/*
 * Safer versions of some standard C library functions. If an
 * out-of-memory condition occurs, these functions will bail out
 * safely; therefore, their return value is guaranteed to be non-NULL.
 */
extern char *pg_strdup(const char *string);
extern void *pg_malloc(size_t size);
extern void *pg_malloc_zero(size_t size);
extern void *pg_calloc(size_t nmemb, size_t size);

extern bool setQFout(const char *fname);

extern void
psql_error(const char *fmt,...)
/* This lets gcc check the format string for consistency. */
__attribute__((format(printf, 1, 2)));

extern void NoticeProcessor(void *arg, const char *message);

extern volatile bool sigint_interrupt_enabled;

extern sigjmp_buf sigint_interrupt_jmp;

extern volatile bool cancel_pressed;

/* Note: cancel_pressed is defined in print.c, see that file for reasons */

extern void setup_cancel_handler(void);

extern void SetCancelConn(void);
extern void ResetCancelConn(void);

extern PGresult *PSQLexec(const char *query, bool start_xact);

extern bool SendQuery(const char *query);

extern bool is_superuser(void);
extern bool standard_strings(void);
extern const char *session_username(void);

extern char *expand_tilde(char **filename);

/* Workarounds for Windows */
/* Probably to be moved up the source tree in the future, perhaps to be replaced by
 * more specific checks like configure-style HAVE_GETTIMEOFDAY macros.
 */
#ifndef WIN32

#include <sys/time.h>

typedef struct timeval TimevalStruct;

#define GETTIMEOFDAY(T) gettimeofday(T, NULL)
#define DIFF_MSEC(T, U) \
	((((int) ((T)->tv_sec - (U)->tv_sec)) * 1000000.0 + \
	  ((int) ((T)->tv_usec - (U)->tv_usec))) / 1000.0)
#else

#include <sys/types.h>
#include <sys/timeb.h>

typedef struct _timeb TimevalStruct;

#define GETTIMEOFDAY(T) _ftime(T)
#define DIFF_MSEC(T, U) \
	(((T)->time - (U)->time) * 1000.0 + \
	 ((T)->millitm - (U)->millitm))
#endif

#endif   /* COMMON_H */
