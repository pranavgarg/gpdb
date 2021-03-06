/*-------------------------------------------------------------------------
 *
 * parse_type.h
 *		handle type operations for parser
 *
 * Portions Copyright (c) 1996-2009, PostgreSQL Global Development Group
 * Portions Copyright (c) 1994, Regents of the University of California
 *
 * $PostgreSQL: pgsql/src/include/parser/parse_type.h,v 1.35 2007/01/05 22:19:57 momjian Exp $
 *
 *-------------------------------------------------------------------------
 */
#ifndef PARSE_TYPE_H
#define PARSE_TYPE_H

#include "access/htup.h"
#include "parser/parse_node.h"


typedef HeapTuple Type;

#define ReleaseType(fmw) ReleaseSysCache((fmw))

extern Oid	LookupTypeName(ParseState *pstate, const TypeName *typname);
extern char *TypeNameToString(const TypeName *typname);
extern char *TypeNameListToString(List *typenames);
extern Oid	typenameTypeId(ParseState *pstate, const TypeName *typname);
extern Type typenameType(ParseState *pstate, const TypeName *typname);
extern int32 typenameTypeMod(ParseState *pstate, const TypeName *typname,
							 Oid typeId);

extern Type typeidType(Oid id);

extern Oid	typeTypeId(Type tp);
extern int16 typeLen(Type t);
extern bool typeByVal(Type t);
extern char typeTypType(Type t);
extern char *typeTypeName(Type t);
extern Oid	typeTypeRelid(Type typ);
extern Datum stringTypeDatum(Type tp, char *string, int32 atttypmod);

extern Oid	typeidTypeRelid(Oid type_id);

extern void parseTypeString(const char *str, Oid *type_id, int32 *typmod);

#define ISCOMPLEX(typid) (typeidTypeRelid(typid) != InvalidOid)

#endif   /* PARSE_TYPE_H */
