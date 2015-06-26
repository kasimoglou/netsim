//
// Generated file, do not edit! Created by opp_msgc 4.4 from src/node/communication/routing/ctpNoe/components/CtpNoePackets.msg.
//

// Disable warnings about unused variables, empty switch stmts, etc:
#ifdef _MSC_VER
#  pragma warning(disable:4101)
#  pragma warning(disable:4065)
#endif

#include <iostream>
#include <sstream>
#include "CtpNoePackets_m.h"

USING_NAMESPACE

// Template rule which fires if a struct or class doesn't have operator<<
template<typename T>
std::ostream& operator<<(std::ostream& out,const T&) {return out;}

// Another default rule (prevents compiler from choosing base class' doPacking())
template<typename T>
void doPacking(cCommBuffer *, T& t) {
    throw cRuntimeError("Parsim error: no doPacking() function for type %s or its base class (check .msg and _m.cc/h files!)",opp_typename(typeid(t)));
}

template<typename T>
void doUnpacking(cCommBuffer *, T& t) {
    throw cRuntimeError("Parsim error: no doUnpacking() function for type %s or its base class (check .msg and _m.cc/h files!)",opp_typename(typeid(t)));
}




neighbor_stat_entry::neighbor_stat_entry()
{
    ll_addr = 0;
    inquality = 0;
}

void doPacking(cCommBuffer *b, neighbor_stat_entry& a)
{
    doPacking(b,a.ll_addr);
    doPacking(b,a.inquality);
}

void doUnpacking(cCommBuffer *b, neighbor_stat_entry& a)
{
    doUnpacking(b,a.ll_addr);
    doUnpacking(b,a.inquality);
}

class neighbor_stat_entryDescriptor : public cClassDescriptor
{
  public:
    neighbor_stat_entryDescriptor();
    virtual ~neighbor_stat_entryDescriptor();

    virtual bool doesSupport(cObject *obj) const;
    virtual const char *getProperty(const char *propertyname) const;
    virtual int getFieldCount(void *object) const;
    virtual const char *getFieldName(void *object, int field) const;
    virtual int findField(void *object, const char *fieldName) const;
    virtual unsigned int getFieldTypeFlags(void *object, int field) const;
    virtual const char *getFieldTypeString(void *object, int field) const;
    virtual const char *getFieldProperty(void *object, int field, const char *propertyname) const;
    virtual int getArraySize(void *object, int field) const;

    virtual std::string getFieldAsString(void *object, int field, int i) const;
    virtual bool setFieldAsString(void *object, int field, int i, const char *value) const;

    virtual const char *getFieldStructName(void *object, int field) const;
    virtual void *getFieldStructPointer(void *object, int field, int i) const;
};

Register_ClassDescriptor(neighbor_stat_entryDescriptor);

neighbor_stat_entryDescriptor::neighbor_stat_entryDescriptor() : cClassDescriptor("neighbor_stat_entry", "")
{
}

neighbor_stat_entryDescriptor::~neighbor_stat_entryDescriptor()
{
}

bool neighbor_stat_entryDescriptor::doesSupport(cObject *obj) const
{
    return dynamic_cast<neighbor_stat_entry *>(obj)!=NULL;
}

const char *neighbor_stat_entryDescriptor::getProperty(const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : NULL;
}

int neighbor_stat_entryDescriptor::getFieldCount(void *object) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 2+basedesc->getFieldCount(object) : 2;
}

unsigned int neighbor_stat_entryDescriptor::getFieldTypeFlags(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeFlags(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
    };
    return (field>=0 && field<2) ? fieldTypeFlags[field] : 0;
}

const char *neighbor_stat_entryDescriptor::getFieldName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldNames[] = {
        "ll_addr",
        "inquality",
    };
    return (field>=0 && field<2) ? fieldNames[field] : NULL;
}

int neighbor_stat_entryDescriptor::findField(void *object, const char *fieldName) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount(object) : 0;
    if (fieldName[0]=='l' && strcmp(fieldName, "ll_addr")==0) return base+0;
    if (fieldName[0]=='i' && strcmp(fieldName, "inquality")==0) return base+1;
    return basedesc ? basedesc->findField(object, fieldName) : -1;
}

const char *neighbor_stat_entryDescriptor::getFieldTypeString(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeString(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldTypeStrings[] = {
        "uint16_t",
        "uint8_t",
    };
    return (field>=0 && field<2) ? fieldTypeStrings[field] : NULL;
}

const char *neighbor_stat_entryDescriptor::getFieldProperty(void *object, int field, const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldProperty(object, field, propertyname);
        field -= basedesc->getFieldCount(object);
    }
    switch (field) {
        default: return NULL;
    }
}

int neighbor_stat_entryDescriptor::getArraySize(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getArraySize(object, field);
        field -= basedesc->getFieldCount(object);
    }
    neighbor_stat_entry *pp = (neighbor_stat_entry *)object; (void)pp;
    switch (field) {
        default: return 0;
    }
}

std::string neighbor_stat_entryDescriptor::getFieldAsString(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldAsString(object,field,i);
        field -= basedesc->getFieldCount(object);
    }
    neighbor_stat_entry *pp = (neighbor_stat_entry *)object; (void)pp;
    switch (field) {
        case 0: return ulong2string(pp->ll_addr);
        case 1: return ulong2string(pp->inquality);
        default: return "";
    }
}

bool neighbor_stat_entryDescriptor::setFieldAsString(void *object, int field, int i, const char *value) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->setFieldAsString(object,field,i,value);
        field -= basedesc->getFieldCount(object);
    }
    neighbor_stat_entry *pp = (neighbor_stat_entry *)object; (void)pp;
    switch (field) {
        case 0: pp->ll_addr = string2ulong(value); return true;
        case 1: pp->inquality = string2ulong(value); return true;
        default: return false;
    }
}

const char *neighbor_stat_entryDescriptor::getFieldStructName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldStructNames[] = {
        NULL,
        NULL,
    };
    return (field>=0 && field<2) ? fieldStructNames[field] : NULL;
}

void *neighbor_stat_entryDescriptor::getFieldStructPointer(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructPointer(object, field, i);
        field -= basedesc->getFieldCount(object);
    }
    neighbor_stat_entry *pp = (neighbor_stat_entry *)object; (void)pp;
    switch (field) {
        default: return NULL;
    }
}

Register_Class(CtpData);

CtpData::CtpData(const char *name, int kind) : RoutingPacket(name,kind)
{
    this->options_var = 0;
    this->thl_var = 0;
    this->etx_var = 0;
    this->origin_var = 0;
    this->originSeqNo_var = 0;
    this->type_var = 0;
}

CtpData::CtpData(const CtpData& other) : RoutingPacket(other)
{
    copy(other);
}

CtpData::~CtpData()
{
}

CtpData& CtpData::operator=(const CtpData& other)
{
    if (this==&other) return *this;
    RoutingPacket::operator=(other);
    copy(other);
    return *this;
}

void CtpData::copy(const CtpData& other)
{
    this->options_var = other.options_var;
    this->thl_var = other.thl_var;
    this->etx_var = other.etx_var;
    this->origin_var = other.origin_var;
    this->originSeqNo_var = other.originSeqNo_var;
    this->type_var = other.type_var;
}

void CtpData::parsimPack(cCommBuffer *b)
{
    RoutingPacket::parsimPack(b);
    doPacking(b,this->options_var);
    doPacking(b,this->thl_var);
    doPacking(b,this->etx_var);
    doPacking(b,this->origin_var);
    doPacking(b,this->originSeqNo_var);
    doPacking(b,this->type_var);
}

void CtpData::parsimUnpack(cCommBuffer *b)
{
    RoutingPacket::parsimUnpack(b);
    doUnpacking(b,this->options_var);
    doUnpacking(b,this->thl_var);
    doUnpacking(b,this->etx_var);
    doUnpacking(b,this->origin_var);
    doUnpacking(b,this->originSeqNo_var);
    doUnpacking(b,this->type_var);
}

uint8_t CtpData::getOptions() const
{
    return options_var;
}

void CtpData::setOptions(uint8_t options)
{
    this->options_var = options;
}

uint8_t CtpData::getThl() const
{
    return thl_var;
}

void CtpData::setThl(uint8_t thl)
{
    this->thl_var = thl;
}

uint16_t CtpData::getEtx() const
{
    return etx_var;
}

void CtpData::setEtx(uint16_t etx)
{
    this->etx_var = etx;
}

uint16_t CtpData::getOrigin() const
{
    return origin_var;
}

void CtpData::setOrigin(uint16_t origin)
{
    this->origin_var = origin;
}

uint8_t CtpData::getOriginSeqNo() const
{
    return originSeqNo_var;
}

void CtpData::setOriginSeqNo(uint8_t originSeqNo)
{
    this->originSeqNo_var = originSeqNo;
}

uint8_t CtpData::getType() const
{
    return type_var;
}

void CtpData::setType(uint8_t type)
{
    this->type_var = type;
}

class CtpDataDescriptor : public cClassDescriptor
{
  public:
    CtpDataDescriptor();
    virtual ~CtpDataDescriptor();

    virtual bool doesSupport(cObject *obj) const;
    virtual const char *getProperty(const char *propertyname) const;
    virtual int getFieldCount(void *object) const;
    virtual const char *getFieldName(void *object, int field) const;
    virtual int findField(void *object, const char *fieldName) const;
    virtual unsigned int getFieldTypeFlags(void *object, int field) const;
    virtual const char *getFieldTypeString(void *object, int field) const;
    virtual const char *getFieldProperty(void *object, int field, const char *propertyname) const;
    virtual int getArraySize(void *object, int field) const;

    virtual std::string getFieldAsString(void *object, int field, int i) const;
    virtual bool setFieldAsString(void *object, int field, int i, const char *value) const;

    virtual const char *getFieldStructName(void *object, int field) const;
    virtual void *getFieldStructPointer(void *object, int field, int i) const;
};

Register_ClassDescriptor(CtpDataDescriptor);

CtpDataDescriptor::CtpDataDescriptor() : cClassDescriptor("CtpData", "RoutingPacket")
{
}

CtpDataDescriptor::~CtpDataDescriptor()
{
}

bool CtpDataDescriptor::doesSupport(cObject *obj) const
{
    return dynamic_cast<CtpData *>(obj)!=NULL;
}

const char *CtpDataDescriptor::getProperty(const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : NULL;
}

int CtpDataDescriptor::getFieldCount(void *object) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 6+basedesc->getFieldCount(object) : 6;
}

unsigned int CtpDataDescriptor::getFieldTypeFlags(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeFlags(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
    };
    return (field>=0 && field<6) ? fieldTypeFlags[field] : 0;
}

const char *CtpDataDescriptor::getFieldName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldNames[] = {
        "options",
        "thl",
        "etx",
        "origin",
        "originSeqNo",
        "type",
    };
    return (field>=0 && field<6) ? fieldNames[field] : NULL;
}

int CtpDataDescriptor::findField(void *object, const char *fieldName) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount(object) : 0;
    if (fieldName[0]=='o' && strcmp(fieldName, "options")==0) return base+0;
    if (fieldName[0]=='t' && strcmp(fieldName, "thl")==0) return base+1;
    if (fieldName[0]=='e' && strcmp(fieldName, "etx")==0) return base+2;
    if (fieldName[0]=='o' && strcmp(fieldName, "origin")==0) return base+3;
    if (fieldName[0]=='o' && strcmp(fieldName, "originSeqNo")==0) return base+4;
    if (fieldName[0]=='t' && strcmp(fieldName, "type")==0) return base+5;
    return basedesc ? basedesc->findField(object, fieldName) : -1;
}

const char *CtpDataDescriptor::getFieldTypeString(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeString(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldTypeStrings[] = {
        "uint8_t",
        "uint8_t",
        "uint16_t",
        "uint16_t",
        "uint8_t",
        "uint8_t",
    };
    return (field>=0 && field<6) ? fieldTypeStrings[field] : NULL;
}

const char *CtpDataDescriptor::getFieldProperty(void *object, int field, const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldProperty(object, field, propertyname);
        field -= basedesc->getFieldCount(object);
    }
    switch (field) {
        default: return NULL;
    }
}

int CtpDataDescriptor::getArraySize(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getArraySize(object, field);
        field -= basedesc->getFieldCount(object);
    }
    CtpData *pp = (CtpData *)object; (void)pp;
    switch (field) {
        default: return 0;
    }
}

std::string CtpDataDescriptor::getFieldAsString(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldAsString(object,field,i);
        field -= basedesc->getFieldCount(object);
    }
    CtpData *pp = (CtpData *)object; (void)pp;
    switch (field) {
        case 0: return ulong2string(pp->getOptions());
        case 1: return ulong2string(pp->getThl());
        case 2: return ulong2string(pp->getEtx());
        case 3: return ulong2string(pp->getOrigin());
        case 4: return ulong2string(pp->getOriginSeqNo());
        case 5: return ulong2string(pp->getType());
        default: return "";
    }
}

bool CtpDataDescriptor::setFieldAsString(void *object, int field, int i, const char *value) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->setFieldAsString(object,field,i,value);
        field -= basedesc->getFieldCount(object);
    }
    CtpData *pp = (CtpData *)object; (void)pp;
    switch (field) {
        case 0: pp->setOptions(string2ulong(value)); return true;
        case 1: pp->setThl(string2ulong(value)); return true;
        case 2: pp->setEtx(string2ulong(value)); return true;
        case 3: pp->setOrigin(string2ulong(value)); return true;
        case 4: pp->setOriginSeqNo(string2ulong(value)); return true;
        case 5: pp->setType(string2ulong(value)); return true;
        default: return false;
    }
}

const char *CtpDataDescriptor::getFieldStructName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldStructNames[] = {
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
    };
    return (field>=0 && field<6) ? fieldStructNames[field] : NULL;
}

void *CtpDataDescriptor::getFieldStructPointer(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructPointer(object, field, i);
        field -= basedesc->getFieldCount(object);
    }
    CtpData *pp = (CtpData *)object; (void)pp;
    switch (field) {
        default: return NULL;
    }
}

Register_Class(CtpBeacon);

CtpBeacon::CtpBeacon(const char *name, int kind) : RoutingPacket(name,kind)
{
    this->options_var = 0;
    this->parent_var = 0;
    this->etx_var = 0;
}

CtpBeacon::CtpBeacon(const CtpBeacon& other) : RoutingPacket(other)
{
    copy(other);
}

CtpBeacon::~CtpBeacon()
{
}

CtpBeacon& CtpBeacon::operator=(const CtpBeacon& other)
{
    if (this==&other) return *this;
    RoutingPacket::operator=(other);
    copy(other);
    return *this;
}

void CtpBeacon::copy(const CtpBeacon& other)
{
    this->options_var = other.options_var;
    this->parent_var = other.parent_var;
    this->etx_var = other.etx_var;
}

void CtpBeacon::parsimPack(cCommBuffer *b)
{
    RoutingPacket::parsimPack(b);
    doPacking(b,this->options_var);
    doPacking(b,this->parent_var);
    doPacking(b,this->etx_var);
}

void CtpBeacon::parsimUnpack(cCommBuffer *b)
{
    RoutingPacket::parsimUnpack(b);
    doUnpacking(b,this->options_var);
    doUnpacking(b,this->parent_var);
    doUnpacking(b,this->etx_var);
}

uint8_t CtpBeacon::getOptions() const
{
    return options_var;
}

void CtpBeacon::setOptions(uint8_t options)
{
    this->options_var = options;
}

uint16_t CtpBeacon::getParent() const
{
    return parent_var;
}

void CtpBeacon::setParent(uint16_t parent)
{
    this->parent_var = parent;
}

uint16_t CtpBeacon::getEtx() const
{
    return etx_var;
}

void CtpBeacon::setEtx(uint16_t etx)
{
    this->etx_var = etx;
}

class CtpBeaconDescriptor : public cClassDescriptor
{
  public:
    CtpBeaconDescriptor();
    virtual ~CtpBeaconDescriptor();

    virtual bool doesSupport(cObject *obj) const;
    virtual const char *getProperty(const char *propertyname) const;
    virtual int getFieldCount(void *object) const;
    virtual const char *getFieldName(void *object, int field) const;
    virtual int findField(void *object, const char *fieldName) const;
    virtual unsigned int getFieldTypeFlags(void *object, int field) const;
    virtual const char *getFieldTypeString(void *object, int field) const;
    virtual const char *getFieldProperty(void *object, int field, const char *propertyname) const;
    virtual int getArraySize(void *object, int field) const;

    virtual std::string getFieldAsString(void *object, int field, int i) const;
    virtual bool setFieldAsString(void *object, int field, int i, const char *value) const;

    virtual const char *getFieldStructName(void *object, int field) const;
    virtual void *getFieldStructPointer(void *object, int field, int i) const;
};

Register_ClassDescriptor(CtpBeaconDescriptor);

CtpBeaconDescriptor::CtpBeaconDescriptor() : cClassDescriptor("CtpBeacon", "RoutingPacket")
{
}

CtpBeaconDescriptor::~CtpBeaconDescriptor()
{
}

bool CtpBeaconDescriptor::doesSupport(cObject *obj) const
{
    return dynamic_cast<CtpBeacon *>(obj)!=NULL;
}

const char *CtpBeaconDescriptor::getProperty(const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : NULL;
}

int CtpBeaconDescriptor::getFieldCount(void *object) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 3+basedesc->getFieldCount(object) : 3;
}

unsigned int CtpBeaconDescriptor::getFieldTypeFlags(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeFlags(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
    };
    return (field>=0 && field<3) ? fieldTypeFlags[field] : 0;
}

const char *CtpBeaconDescriptor::getFieldName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldNames[] = {
        "options",
        "parent",
        "etx",
    };
    return (field>=0 && field<3) ? fieldNames[field] : NULL;
}

int CtpBeaconDescriptor::findField(void *object, const char *fieldName) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount(object) : 0;
    if (fieldName[0]=='o' && strcmp(fieldName, "options")==0) return base+0;
    if (fieldName[0]=='p' && strcmp(fieldName, "parent")==0) return base+1;
    if (fieldName[0]=='e' && strcmp(fieldName, "etx")==0) return base+2;
    return basedesc ? basedesc->findField(object, fieldName) : -1;
}

const char *CtpBeaconDescriptor::getFieldTypeString(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeString(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldTypeStrings[] = {
        "uint8_t",
        "uint16_t",
        "uint16_t",
    };
    return (field>=0 && field<3) ? fieldTypeStrings[field] : NULL;
}

const char *CtpBeaconDescriptor::getFieldProperty(void *object, int field, const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldProperty(object, field, propertyname);
        field -= basedesc->getFieldCount(object);
    }
    switch (field) {
        default: return NULL;
    }
}

int CtpBeaconDescriptor::getArraySize(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getArraySize(object, field);
        field -= basedesc->getFieldCount(object);
    }
    CtpBeacon *pp = (CtpBeacon *)object; (void)pp;
    switch (field) {
        default: return 0;
    }
}

std::string CtpBeaconDescriptor::getFieldAsString(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldAsString(object,field,i);
        field -= basedesc->getFieldCount(object);
    }
    CtpBeacon *pp = (CtpBeacon *)object; (void)pp;
    switch (field) {
        case 0: return ulong2string(pp->getOptions());
        case 1: return ulong2string(pp->getParent());
        case 2: return ulong2string(pp->getEtx());
        default: return "";
    }
}

bool CtpBeaconDescriptor::setFieldAsString(void *object, int field, int i, const char *value) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->setFieldAsString(object,field,i,value);
        field -= basedesc->getFieldCount(object);
    }
    CtpBeacon *pp = (CtpBeacon *)object; (void)pp;
    switch (field) {
        case 0: pp->setOptions(string2ulong(value)); return true;
        case 1: pp->setParent(string2ulong(value)); return true;
        case 2: pp->setEtx(string2ulong(value)); return true;
        default: return false;
    }
}

const char *CtpBeaconDescriptor::getFieldStructName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldStructNames[] = {
        NULL,
        NULL,
        NULL,
    };
    return (field>=0 && field<3) ? fieldStructNames[field] : NULL;
}

void *CtpBeaconDescriptor::getFieldStructPointer(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructPointer(object, field, i);
        field -= basedesc->getFieldCount(object);
    }
    CtpBeacon *pp = (CtpBeacon *)object; (void)pp;
    switch (field) {
        default: return NULL;
    }
}

Register_Class(CtpLe);

CtpLe::CtpLe(const char *name, int kind) : CtpBeacon(name,kind)
{
    this->flags_var = 0;
    this->seq_var = 0;
    linkest_footer_arraysize = 0;
    this->linkest_footer_var = 0;
}

CtpLe::CtpLe(const CtpLe& other) : CtpBeacon(other)
{
    linkest_footer_arraysize = 0;
    this->linkest_footer_var = 0;
    copy(other);
}

CtpLe::~CtpLe()
{
    delete [] linkest_footer_var;
}

CtpLe& CtpLe::operator=(const CtpLe& other)
{
    if (this==&other) return *this;
    CtpBeacon::operator=(other);
    copy(other);
    return *this;
}

void CtpLe::copy(const CtpLe& other)
{
    this->flags_var = other.flags_var;
    this->seq_var = other.seq_var;
    delete [] this->linkest_footer_var;
    this->linkest_footer_var = (other.linkest_footer_arraysize==0) ? NULL : new neighbor_stat_entry[other.linkest_footer_arraysize];
    linkest_footer_arraysize = other.linkest_footer_arraysize;
    for (unsigned int i=0; i<linkest_footer_arraysize; i++)
        this->linkest_footer_var[i] = other.linkest_footer_var[i];
}

void CtpLe::parsimPack(cCommBuffer *b)
{
    CtpBeacon::parsimPack(b);
    doPacking(b,this->flags_var);
    doPacking(b,this->seq_var);
    b->pack(linkest_footer_arraysize);
    doPacking(b,this->linkest_footer_var,linkest_footer_arraysize);
}

void CtpLe::parsimUnpack(cCommBuffer *b)
{
    CtpBeacon::parsimUnpack(b);
    doUnpacking(b,this->flags_var);
    doUnpacking(b,this->seq_var);
    delete [] this->linkest_footer_var;
    b->unpack(linkest_footer_arraysize);
    if (linkest_footer_arraysize==0) {
        this->linkest_footer_var = 0;
    } else {
        this->linkest_footer_var = new neighbor_stat_entry[linkest_footer_arraysize];
        doUnpacking(b,this->linkest_footer_var,linkest_footer_arraysize);
    }
}

uint8_t CtpLe::getFlags() const
{
    return flags_var;
}

void CtpLe::setFlags(uint8_t flags)
{
    this->flags_var = flags;
}

uint8_t CtpLe::getSeq() const
{
    return seq_var;
}

void CtpLe::setSeq(uint8_t seq)
{
    this->seq_var = seq;
}

void CtpLe::setLinkest_footerArraySize(unsigned int size)
{
    neighbor_stat_entry *linkest_footer_var2 = (size==0) ? NULL : new neighbor_stat_entry[size];
    unsigned int sz = linkest_footer_arraysize < size ? linkest_footer_arraysize : size;
    for (unsigned int i=0; i<sz; i++)
        linkest_footer_var2[i] = this->linkest_footer_var[i];
    linkest_footer_arraysize = size;
    delete [] this->linkest_footer_var;
    this->linkest_footer_var = linkest_footer_var2;
}

unsigned int CtpLe::getLinkest_footerArraySize() const
{
    return linkest_footer_arraysize;
}

neighbor_stat_entry& CtpLe::getLinkest_footer(unsigned int k)
{
    if (k>=linkest_footer_arraysize) throw cRuntimeError("Array of size %d indexed by %d", linkest_footer_arraysize, k);
    return linkest_footer_var[k];
}

void CtpLe::setLinkest_footer(unsigned int k, const neighbor_stat_entry& linkest_footer)
{
    if (k>=linkest_footer_arraysize) throw cRuntimeError("Array of size %d indexed by %d", linkest_footer_arraysize, k);
    this->linkest_footer_var[k] = linkest_footer;
}

class CtpLeDescriptor : public cClassDescriptor
{
  public:
    CtpLeDescriptor();
    virtual ~CtpLeDescriptor();

    virtual bool doesSupport(cObject *obj) const;
    virtual const char *getProperty(const char *propertyname) const;
    virtual int getFieldCount(void *object) const;
    virtual const char *getFieldName(void *object, int field) const;
    virtual int findField(void *object, const char *fieldName) const;
    virtual unsigned int getFieldTypeFlags(void *object, int field) const;
    virtual const char *getFieldTypeString(void *object, int field) const;
    virtual const char *getFieldProperty(void *object, int field, const char *propertyname) const;
    virtual int getArraySize(void *object, int field) const;

    virtual std::string getFieldAsString(void *object, int field, int i) const;
    virtual bool setFieldAsString(void *object, int field, int i, const char *value) const;

    virtual const char *getFieldStructName(void *object, int field) const;
    virtual void *getFieldStructPointer(void *object, int field, int i) const;
};

Register_ClassDescriptor(CtpLeDescriptor);

CtpLeDescriptor::CtpLeDescriptor() : cClassDescriptor("CtpLe", "CtpBeacon")
{
}

CtpLeDescriptor::~CtpLeDescriptor()
{
}

bool CtpLeDescriptor::doesSupport(cObject *obj) const
{
    return dynamic_cast<CtpLe *>(obj)!=NULL;
}

const char *CtpLeDescriptor::getProperty(const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : NULL;
}

int CtpLeDescriptor::getFieldCount(void *object) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 3+basedesc->getFieldCount(object) : 3;
}

unsigned int CtpLeDescriptor::getFieldTypeFlags(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeFlags(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISARRAY | FD_ISCOMPOUND,
    };
    return (field>=0 && field<3) ? fieldTypeFlags[field] : 0;
}

const char *CtpLeDescriptor::getFieldName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldNames[] = {
        "flags",
        "seq",
        "linkest_footer",
    };
    return (field>=0 && field<3) ? fieldNames[field] : NULL;
}

int CtpLeDescriptor::findField(void *object, const char *fieldName) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount(object) : 0;
    if (fieldName[0]=='f' && strcmp(fieldName, "flags")==0) return base+0;
    if (fieldName[0]=='s' && strcmp(fieldName, "seq")==0) return base+1;
    if (fieldName[0]=='l' && strcmp(fieldName, "linkest_footer")==0) return base+2;
    return basedesc ? basedesc->findField(object, fieldName) : -1;
}

const char *CtpLeDescriptor::getFieldTypeString(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeString(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldTypeStrings[] = {
        "uint8_t",
        "uint8_t",
        "neighbor_stat_entry",
    };
    return (field>=0 && field<3) ? fieldTypeStrings[field] : NULL;
}

const char *CtpLeDescriptor::getFieldProperty(void *object, int field, const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldProperty(object, field, propertyname);
        field -= basedesc->getFieldCount(object);
    }
    switch (field) {
        default: return NULL;
    }
}

int CtpLeDescriptor::getArraySize(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getArraySize(object, field);
        field -= basedesc->getFieldCount(object);
    }
    CtpLe *pp = (CtpLe *)object; (void)pp;
    switch (field) {
        case 2: return pp->getLinkest_footerArraySize();
        default: return 0;
    }
}

std::string CtpLeDescriptor::getFieldAsString(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldAsString(object,field,i);
        field -= basedesc->getFieldCount(object);
    }
    CtpLe *pp = (CtpLe *)object; (void)pp;
    switch (field) {
        case 0: return ulong2string(pp->getFlags());
        case 1: return ulong2string(pp->getSeq());
        case 2: {std::stringstream out; out << pp->getLinkest_footer(i); return out.str();}
        default: return "";
    }
}

bool CtpLeDescriptor::setFieldAsString(void *object, int field, int i, const char *value) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->setFieldAsString(object,field,i,value);
        field -= basedesc->getFieldCount(object);
    }
    CtpLe *pp = (CtpLe *)object; (void)pp;
    switch (field) {
        case 0: pp->setFlags(string2ulong(value)); return true;
        case 1: pp->setSeq(string2ulong(value)); return true;
        default: return false;
    }
}

const char *CtpLeDescriptor::getFieldStructName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldStructNames[] = {
        NULL,
        NULL,
        "neighbor_stat_entry",
    };
    return (field>=0 && field<3) ? fieldStructNames[field] : NULL;
}

void *CtpLeDescriptor::getFieldStructPointer(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructPointer(object, field, i);
        field -= basedesc->getFieldCount(object);
    }
    CtpLe *pp = (CtpLe *)object; (void)pp;
    switch (field) {
        case 2: return (void *)(&pp->getLinkest_footer(i)); break;
        default: return NULL;
    }
}

Register_Class(CtpNotification);

CtpNotification::CtpNotification(const char *name, int kind) : cMessage(name,kind)
{
    this->cnType_var = 0;
    this->cnInterface_var = 0;
    this->cnEvent_var = 0;
    this->cnCommand_var = 0;
    this->error_var = 0;
}

CtpNotification::CtpNotification(const CtpNotification& other) : cMessage(other)
{
    copy(other);
}

CtpNotification::~CtpNotification()
{
}

CtpNotification& CtpNotification::operator=(const CtpNotification& other)
{
    if (this==&other) return *this;
    cMessage::operator=(other);
    copy(other);
    return *this;
}

void CtpNotification::copy(const CtpNotification& other)
{
    this->cnType_var = other.cnType_var;
    this->cnInterface_var = other.cnInterface_var;
    this->cnEvent_var = other.cnEvent_var;
    this->cnCommand_var = other.cnCommand_var;
    this->error_var = other.error_var;
}

void CtpNotification::parsimPack(cCommBuffer *b)
{
    cMessage::parsimPack(b);
    doPacking(b,this->cnType_var);
    doPacking(b,this->cnInterface_var);
    doPacking(b,this->cnEvent_var);
    doPacking(b,this->cnCommand_var);
    doPacking(b,this->error_var);
}

void CtpNotification::parsimUnpack(cCommBuffer *b)
{
    cMessage::parsimUnpack(b);
    doUnpacking(b,this->cnType_var);
    doUnpacking(b,this->cnInterface_var);
    doUnpacking(b,this->cnEvent_var);
    doUnpacking(b,this->cnCommand_var);
    doUnpacking(b,this->error_var);
}

int CtpNotification::getCnType() const
{
    return cnType_var;
}

void CtpNotification::setCnType(int cnType)
{
    this->cnType_var = cnType;
}

int CtpNotification::getCnInterface() const
{
    return cnInterface_var;
}

void CtpNotification::setCnInterface(int cnInterface)
{
    this->cnInterface_var = cnInterface;
}

int CtpNotification::getCnEvent() const
{
    return cnEvent_var;
}

void CtpNotification::setCnEvent(int cnEvent)
{
    this->cnEvent_var = cnEvent;
}

int CtpNotification::getCnCommand() const
{
    return cnCommand_var;
}

void CtpNotification::setCnCommand(int cnCommand)
{
    this->cnCommand_var = cnCommand;
}

uint8_t CtpNotification::getError() const
{
    return error_var;
}

void CtpNotification::setError(uint8_t error)
{
    this->error_var = error;
}

class CtpNotificationDescriptor : public cClassDescriptor
{
  public:
    CtpNotificationDescriptor();
    virtual ~CtpNotificationDescriptor();

    virtual bool doesSupport(cObject *obj) const;
    virtual const char *getProperty(const char *propertyname) const;
    virtual int getFieldCount(void *object) const;
    virtual const char *getFieldName(void *object, int field) const;
    virtual int findField(void *object, const char *fieldName) const;
    virtual unsigned int getFieldTypeFlags(void *object, int field) const;
    virtual const char *getFieldTypeString(void *object, int field) const;
    virtual const char *getFieldProperty(void *object, int field, const char *propertyname) const;
    virtual int getArraySize(void *object, int field) const;

    virtual std::string getFieldAsString(void *object, int field, int i) const;
    virtual bool setFieldAsString(void *object, int field, int i, const char *value) const;

    virtual const char *getFieldStructName(void *object, int field) const;
    virtual void *getFieldStructPointer(void *object, int field, int i) const;
};

Register_ClassDescriptor(CtpNotificationDescriptor);

CtpNotificationDescriptor::CtpNotificationDescriptor() : cClassDescriptor("CtpNotification", "cMessage")
{
}

CtpNotificationDescriptor::~CtpNotificationDescriptor()
{
}

bool CtpNotificationDescriptor::doesSupport(cObject *obj) const
{
    return dynamic_cast<CtpNotification *>(obj)!=NULL;
}

const char *CtpNotificationDescriptor::getProperty(const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : NULL;
}

int CtpNotificationDescriptor::getFieldCount(void *object) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 5+basedesc->getFieldCount(object) : 5;
}

unsigned int CtpNotificationDescriptor::getFieldTypeFlags(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeFlags(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
    };
    return (field>=0 && field<5) ? fieldTypeFlags[field] : 0;
}

const char *CtpNotificationDescriptor::getFieldName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldNames[] = {
        "cnType",
        "cnInterface",
        "cnEvent",
        "cnCommand",
        "error",
    };
    return (field>=0 && field<5) ? fieldNames[field] : NULL;
}

int CtpNotificationDescriptor::findField(void *object, const char *fieldName) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount(object) : 0;
    if (fieldName[0]=='c' && strcmp(fieldName, "cnType")==0) return base+0;
    if (fieldName[0]=='c' && strcmp(fieldName, "cnInterface")==0) return base+1;
    if (fieldName[0]=='c' && strcmp(fieldName, "cnEvent")==0) return base+2;
    if (fieldName[0]=='c' && strcmp(fieldName, "cnCommand")==0) return base+3;
    if (fieldName[0]=='e' && strcmp(fieldName, "error")==0) return base+4;
    return basedesc ? basedesc->findField(object, fieldName) : -1;
}

const char *CtpNotificationDescriptor::getFieldTypeString(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldTypeString(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldTypeStrings[] = {
        "int",
        "int",
        "int",
        "int",
        "uint8_t",
    };
    return (field>=0 && field<5) ? fieldTypeStrings[field] : NULL;
}

const char *CtpNotificationDescriptor::getFieldProperty(void *object, int field, const char *propertyname) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldProperty(object, field, propertyname);
        field -= basedesc->getFieldCount(object);
    }
    switch (field) {
        case 0:
            if (!strcmp(propertyname,"enum")) return "Notification_type";
            return NULL;
        case 1:
            if (!strcmp(propertyname,"enum")) return "Notification_interface";
            return NULL;
        case 2:
            if (!strcmp(propertyname,"enum")) return "Notification_event";
            return NULL;
        case 3:
            if (!strcmp(propertyname,"enum")) return "Notification_command";
            return NULL;
        case 4:
            if (!strcmp(propertyname,"enum")) return "tos_err_types";
            return NULL;
        default: return NULL;
    }
}

int CtpNotificationDescriptor::getArraySize(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getArraySize(object, field);
        field -= basedesc->getFieldCount(object);
    }
    CtpNotification *pp = (CtpNotification *)object; (void)pp;
    switch (field) {
        default: return 0;
    }
}

std::string CtpNotificationDescriptor::getFieldAsString(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldAsString(object,field,i);
        field -= basedesc->getFieldCount(object);
    }
    CtpNotification *pp = (CtpNotification *)object; (void)pp;
    switch (field) {
        case 0: return long2string(pp->getCnType());
        case 1: return long2string(pp->getCnInterface());
        case 2: return long2string(pp->getCnEvent());
        case 3: return long2string(pp->getCnCommand());
        case 4: return ulong2string(pp->getError());
        default: return "";
    }
}

bool CtpNotificationDescriptor::setFieldAsString(void *object, int field, int i, const char *value) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->setFieldAsString(object,field,i,value);
        field -= basedesc->getFieldCount(object);
    }
    CtpNotification *pp = (CtpNotification *)object; (void)pp;
    switch (field) {
        case 0: pp->setCnType(string2long(value)); return true;
        case 1: pp->setCnInterface(string2long(value)); return true;
        case 2: pp->setCnEvent(string2long(value)); return true;
        case 3: pp->setCnCommand(string2long(value)); return true;
        case 4: pp->setError(string2ulong(value)); return true;
        default: return false;
    }
}

const char *CtpNotificationDescriptor::getFieldStructName(void *object, int field) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructName(object, field);
        field -= basedesc->getFieldCount(object);
    }
    static const char *fieldStructNames[] = {
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
    };
    return (field>=0 && field<5) ? fieldStructNames[field] : NULL;
}

void *CtpNotificationDescriptor::getFieldStructPointer(void *object, int field, int i) const
{
    cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount(object))
            return basedesc->getFieldStructPointer(object, field, i);
        field -= basedesc->getFieldCount(object);
    }
    CtpNotification *pp = (CtpNotification *)object; (void)pp;
    switch (field) {
        default: return NULL;
    }
}


