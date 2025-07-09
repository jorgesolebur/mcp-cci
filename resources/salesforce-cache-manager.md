# Salesforce Cache Manager Framework

## Overview

The Salesforce Cache Manager Framework provides a robust and flexible way to handle caching in a Salesforce org using Platform Cache. This framework helps reduce SOQL queries and improve performance by caching frequently accessed data across transactions.

## Why Use This Framework?

Before implementing caching, it's important to understand how Apex handles static variables and their limitations:

- **Static Variables**: While useful for reducing overhead within a single transaction, they only last for the duration of the transaction
- **Transaction Limitations**: Static variables still require overhead to populate in every transaction
- **Cross-Transaction Needs**: Ideally, we should cache data across transactions for better performance

Salesforce's Platform Cache addresses these limitations by providing persistent storage across transactions.

## Cache Types

The framework supports three types of caches:

### 1. Organization Cache
- **Scope**: Available to all users in the org
- **Use Case**: Non-user-specific data that can be shared across all users
- **Example**: Queue data, configuration settings, picklist values

### 2. Session Cache
- **Scope**: Available only to the specific user's session
- **Use Case**: User-specific data that should persist across transactions
- **Example**: User preferences, personalized settings

### 3. Transaction Cache
- **Scope**: Available only within a single Apex transaction
- **Use Case**: Preventing duplicate SOQL queries within the same execution context
- **Performance**: Extremely fast (just a map in memory)
- **Lifecycle**: Data is discarded when the transaction ends

## Configuration Management

### CacheConfiguration__mdt Custom Metadata Type

The framework uses custom metadata for declarative control:

**Key Benefits:**
- **No Code Changes**: Modify cache behavior without touching Apex code
- **Admin-Friendly**: Change settings through Setup UI
- **Flexible Control**: Enable/disable caches, modify TTL, control mutability

**Configuration Options:**
- `IsEnabled__c`: Enable/disable the cache
- `PlatformCacheTimeToLive__c`: Set cache expiration time
- `IsImmutable__c`: Control whether cached values can be overwritten

**Sample Records:**
- Organization cache configuration
- Session cache configuration  
- Transaction cache configuration

### CacheValue__mdt Custom Metadata Type

For declarative cache population:

**When to Use:**
- Data that doesn't change frequently
- Need admin-friendly override capability
- Static data values that can be predefined

**Benefits:**
- Automatic cache loading at transaction start
- No code deployment for data changes
- Emergency override capability

## Usage Examples

### Transaction Cache

```apex
// Get transaction cache instance
CacheManager.TransactionCache cache = CacheManager.getTransactionCache();

// Check if data exists
if (cache.contains('queue_data')) {
    // Retrieve cached data
    List<Group> queues = (List<Group>) cache.get('queue_data');
    return queues;
} else {
    // Query and cache data
    List<Group> queues = [SELECT Id, Name FROM Group WHERE Type = 'Queue'];
    cache.put('queue_data', queues);
    return queues;
}
```

### Organization Cache

```apex
// Get organization cache instance
CacheManager.OrganizationCache cache = CacheManager.getOrganizationCache();

// Check and retrieve/store data
if (cache.contains('global_settings')) {
    return (Map<String, Object>) cache.get('global_settings');
} else {
    Map<String, Object> settings = queryGlobalSettings();
    cache.put('global_settings', settings);
    return settings;
}
```

### Session Cache

```apex
// Get session cache instance
CacheManager.SessionCache cache = CacheManager.getSessionCache();

// User-specific caching
String userKey = 'user_preferences_' + UserInfo.getUserId();
if (cache.contains(userKey)) {
    return (UserPreferences__c) cache.get(userKey);
} else {
    UserPreferences__c prefs = queryUserPreferences();
    cache.put(userKey, prefs);
    return prefs;
}
```

## Implementation Best Practices

### 1. Cache Key Naming
- Use descriptive, unique keys
- Consider prefixing with functionality (e.g., 'queues_', 'users_')
- Include relevant identifiers when needed

### 2. Data Validation
- Always validate cached data before use
- Check for null values after retrieval
- Implement fallback mechanisms

### 3. Cache Invalidation
- Plan for cache invalidation strategies
- Consider TTL settings based on data change frequency
- Implement manual cache clearing when needed

### 4. Performance Considerations
- Use Transaction Cache for single-transaction data
- Use Organization Cache for shared, infrequently changing data
- Use Session Cache for user-specific data

### 5. Error Handling
```apex
try {
    if (cache.contains(key)) {
        return cache.get(key);
    }
} catch (Exception e) {
    // Log error and fall back to query
    System.debug('Cache retrieval failed: ' + e.getMessage());
}
// Fallback to direct query
return queryDataDirectly();
```

## Common Use Cases

### 1. Queue Data Caching
```apex
public static List<Group> getCachedQueues() {
    CacheManager.TransactionCache cache = CacheManager.getTransactionCache();
    String key = 'organization_queues';
    
    if (cache.contains(key)) {
        return (List<Group>) cache.get(key);
    }
    
    List<Group> queues = [SELECT Id, Name, DeveloperName FROM Group WHERE Type = 'Queue'];
    cache.put(key, queues);
    return queues;
}
```

### 2. Custom Settings Caching
```apex
public static CustomSettings__c getCachedSettings() {
    CacheManager.OrganizationCache cache = CacheManager.getOrganizationCache();
    String key = 'org_custom_settings';
    
    if (cache.contains(key)) {
        return (CustomSettings__c) cache.get(key);
    }
    
    CustomSettings__c settings = CustomSettings__c.getOrgDefaults();
    cache.put(key, settings);
    return settings;
}
```

### 3. User Role Hierarchy Caching
```apex
public static Map<Id, UserRole> getCachedUserRoles() {
    CacheManager.SessionCache cache = CacheManager.getSessionCache();
    String key = 'user_roles_' + UserInfo.getUserId();
    
    if (cache.contains(key)) {
        return (Map<Id, UserRole>) cache.get(key);
    }
    
    Map<Id, UserRole> roles = new Map<Id, UserRole>([SELECT Id, Name FROM UserRole]);
    cache.put(key, roles);
    return roles;
}
```

## Monitoring and Debugging

### Cache Hit/Miss Tracking
Consider implementing logging to track cache effectiveness:

```apex
public static void logCacheHit(String key, String cacheType) {
    System.debug('Cache HIT: ' + cacheType + ' - Key: ' + key);
}

public static void logCacheMiss(String key, String cacheType) {
    System.debug('Cache MISS: ' + cacheType + ' - Key: ' + key);
}
```

### Performance Monitoring
- Monitor cache hit rates
- Track query reduction
- Measure transaction execution times

## Security Considerations

- **Data Sensitivity**: Don't cache sensitive data in Organization Cache
- **User Context**: Ensure Session Cache data is properly scoped
- **Access Control**: Respect field-level and object-level permissions

## Additional Resources

- [Salesforce Platform Cache Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_overview.htm)
- [Joys of Apex: Building a Flexible Caching System](https://www.jamessimone.net/blog/joys-of-apex/iteratively-building-a-flexible-caching-system/)
- [Platform Cache Best Practices](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_best_practices.htm)

## Framework Integration

This framework integrates seamlessly with:
- Trigger frameworks
- Service layer patterns
- Selector pattern implementations
- Custom metadata type configurations

Use this framework to optimize your Salesforce applications by reducing redundant SOQL queries and improving overall performance through strategic caching.