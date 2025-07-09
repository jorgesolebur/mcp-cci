# Salesforce Triggers Development Guidelines

## Project Context
This project is focused on developing **2GP (Second Generation Package) Managed Packages** for Salesforce. Multiple managed packages will be developed under the same namespace, requiring special consideration for:

- **Package boundaries**: Triggers and handlers must be designed to work within managed package constraints
- **Cross-package dependencies**: Careful management of dependencies between different managed packages
- **Namespace considerations**: All components must be properly namespaced for managed package distribution
- **Subscriber org compatibility**: Code must work reliably across different subscriber org configurations
- **API versioning**: Consistent API version management across all package components

## Overview
This document provides comprehensive guidelines for developing Apex triggers using our **Metadata-Driven Trigger Framework** specifically designed for 2GP managed package development. This framework enables multiple managed packages to safely execute trigger logic on the same sObject through dynamic class loading and metadata configuration.

## Metadata-Driven Trigger Framework

### Purpose
Managing triggers across multiple managed packages in Salesforce can be complex and error-prone, especially when multiple packages interact with the same sObject. The Metadata-Driven Trigger Framework solves this by:

- **One Trigger Per Object**: Use just one Apex trigger per object, even if multiple packages need to run logic on that object
- **Separation of Concerns**: Keep trigger logic separate from the trigger file for easier management and maintenance
- **Modular Design**: Make trigger setup modular and flexible, so each package can plug in its own logic safely
- **Metadata-Driven**: Use Custom Metadata to manage execution dynamically and declaratively

### Framework Architecture

#### Core Components
The trigger framework includes these key components:

1. **TriggerHandler.cls**: Manages trigger context and execution flow, provides bypass and loop control functionality
2. **MetadataTriggerHandler.cls**: Extended functionality for metadata-driven triggers, allows dynamic trigger behavior
3. **MetadataTriggerService.cls**: Service layer for metadata-driven trigger functionality
4. **Metadata_Driven_Trigger__mdt**: Custom metadata type to manage and control trigger execution across packages

#### Dynamic Class Loading
The framework uses `Type.forName()` to dynamically load and execute handler classes:

```apex
activeHandler = (TriggerHandler) Type.forName(trigger.NamespacePrefix, trigger.class__c).newInstance();
```

- `Type.forName(namespace, className)` - Dynamically gets a reference to the Apex class
- `trigger.NamespacePrefix` - The namespace of the package (can be blank in non-namespace orgs)
- `trigger.class__c` - The API name of the Apex trigger handler class (stored in metadata)
- `.newInstance()` - Creates a new instance of that class
- `(TriggerHandler)` - Casts the instance to call standard methods like `beforeInsert()` or `afterUpdate()`

## Implementation Patterns

### Scenario 1: Creating Your First Trigger for an Object

When creating a trigger for the first time, you need to create:
1. **1 Apex Trigger** - Contains only the MetadataTriggerHandler call
2. **1 Object Domain Class** - Contains trigger logic and calls service methods
3. **1 Object Service Class** - Contains business logic implementation
4. **1 Metadata_Driven_Trigger__mdt Record** - Configures the trigger execution

#### Package Location Rules
- **Custom Objects**: Trigger is defined in the package where the custom object was initially created
- **Standard Objects**: Trigger is defined in the Foundation (p1) package
- **Important**: If you define it in a level above, lower-level packages will never be able to create triggers!

#### Naming Conventions
- **Apex Trigger**: `<sObjectName>Trigger` (e.g., `AccountTrigger`)
- **Object Domain Class**: `<packageName><sObjectName>TriggerHandler` (e.g., `p1AccountTriggerHandler`)
- **Service Class**: `<packageName><sObjectName>Service` (e.g., `p1AccountService`)

#### Apex Trigger Template
```apex
trigger AccountTrigger on Account(before insert, after insert, before update, after update, before delete, after delete, after undelete) {
    new MetadataTriggerHandler().run();
}
```

#### Object Domain Class Template
```apex
@namespaceAccessible
public with sharing class p1AccountTriggerHandler extends TriggerHandler {
    private List<Account> triggerNew;
    private List<Account> triggerOld;
    private Map<Id, Account> triggerMapNew;
    private Map<Id, Account> triggerMapOld;
    
    /**
     * @description Constructor that sets class variables based on Trigger context vars
     */
    @namespaceAccessible
    public p1AccountTriggerHandler() {
        this.triggerOld = (List<Account>) Trigger.old;
        this.triggerNew = (List<Account>) Trigger.new;
        this.triggerMapNew = (Map<Id, Account>) Trigger.newMap;
        this.triggerMapOld = (Map<Id, Account>) Trigger.oldMap;
    }
    
    public override void beforeInsert() {
        p1AccountService.changeDescription(this.triggerNew);
    }
    
    public override void afterUpdate() {
        p1AccountService.updateRelatedRecords(this.triggerNew);
    }
}
```

#### Service Class Template
```apex
public with sharing class p1AccountService {
    
    public static void changeDescription(List<Account> accounts) {
        try {
            for (Account acc : accounts) {
                Nebula.Logger.info('Account Object ' + acc);
                if (acc.Description == null) {
                    acc.Description = 'This is a patient Account';
                }
            }
        } catch (Exception e) {
            Nebula.Logger.error('Error in changeDescription: ' + e.getMessage());
        }
    }
    
    public static void updateRelatedRecords(List<Account> accounts) {
        // Get the shared Unit of Work instance
        UnitOfWork uow = UnitOfWorkManager.getUnitOfWork(AccessLevel.SYSTEM_MODE);
        
        Set<Id> accountIds = new Set<Id>();
        for (Account acc : accounts) {
            accountIds.add(acc.Id);
        }
        
        // Query related records
        List<Contact> contactsToUpdate = [
            SELECT Id, Description 
            FROM Contact 
            WHERE AccountId IN :accountIds
        ];
        
        for (Contact con : contactsToUpdate) {
            con.Description = 'Updated via trigger';
            uow.registerClean(con);
        }
        
        // No need to call commitWork() - handled by MetadataTriggerHandler
    }
}
```

### Scenario 2: Adding Trigger Logic to Existing Object

When a trigger already exists in another package, you create additional logic without modifying existing code:

1. **1 New Object Domain Class** - In your package
2. **1 New Object Service Class** - In your package  
3. **1 New Metadata_Driven_Trigger__mdt Record** - With proper execution order

#### Example: Adding p2 Package Logic
```apex
@namespaceAccessible
public with sharing class p2AccountTriggerHandler extends TriggerHandler {
    private List<Account> triggerNew;
    private List<Account> triggerOld;
    private Map<Id, Account> triggerMapNew;
    private Map<Id, Account> triggerMapOld;
    
    @namespaceAccessible
    public p2AccountTriggerHandler() {
        this.triggerOld = (List<Account>) Trigger.old;
        this.triggerNew = (List<Account>) Trigger.new;
        this.triggerMapNew = (Map<Id, Account>) Trigger.newMap;
        this.triggerMapOld = (Map<Id, Account>) Trigger.oldMap;
    }
    
    public override void beforeUpdate() {
        p2AccountService.updateIndustry(this.triggerNew);
        p2AccountService.updateRelatedRecords(this.triggerNew);
    }
}
```

### Metadata_Driven_Trigger__mdt Configuration

Each trigger handler must have a corresponding metadata record with:
- **Object__c**: The API name of the object (e.g., "Account")
- **Class__c**: The Object Domain class name (e.g., "p1AccountTriggerHandler")
- **Execution_Order__c**: Used to sequence execution across packages
- **Enabled__c**: Controls whether the trigger executes

## Framework Features

### MaxLoopCount Protection
To prevent recursion, you can set a max loop count for Trigger Handler:

```apex
@namespaceAccessible
public class p1AccountTriggerHandler extends TriggerHandler {
    @namespaceAccessible
    public p1AccountTriggerHandler() {
        this.setMaxLoopCount(1); // Ensures trigger runs only once
    }
    
    public override void afterUpdate() {
        List<Account> accs = [SELECT Id FROM Account WHERE Id IN :Trigger.newMap.keySet()];
        update accs; // This will throw after this update
    }
}
```

### Bypass API
Control trigger execution dynamically:

```apex
@namespaceAccessible
public class OpportunityTriggerHandler extends TriggerHandler {
    public override void afterUpdate() {
        List<Opportunity> opps = [SELECT Id, AccountId FROM Opportunity WHERE Id IN :Trigger.newMap.keySet()];
        Account acc = [SELECT Id, Name FROM Account WHERE Id = :opps.get(0).AccountId];
        
        TriggerHandler.bypass('p1AccountTriggerHandler');
        acc.Name = 'No Trigger';
        update acc; // Won't invoke the p1AccountTriggerHandler
        
        TriggerHandler.clearBypass('p1AccountTriggerHandler');
        acc.Name = 'With Trigger';
        update acc; // Will invoke the AccountTriggerHandler
    }
}
```

Additional bypass methods:
```apex
// Check if a handler is bypassed
if (TriggerHandler.isBypassed('p1AccountTriggerHandler')) {
    // Do something if the Account trigger handler is bypassed
}

// Clear all bypasses for the transaction
TriggerHandler.clearAllBypasses();
```

### Unit of Work Integration
For related record operations, use the Unit of Work framework:

```apex
public static void updateRelatedRecords(List<Account> accounts) {
    // Get the shared Unit of Work instance, Trigger execution is always in SYSTEM MODE
    UnitOfWork uow = UnitOfWorkManager.getUnitOfWork(AccessLevel.SYSTEM_MODE);
    
    for (Account acc : accounts) {
        // Create related contact
        Contact relatedContact = new Contact(
            FirstName = 'Auto',
            LastName = 'Generated',
            Email = 'auto@' + acc.Name.toLowerCase() + '.com'
        );
        // Register the relationship - UoW will handle the reference
        uow.registerDirty(acc, relatedContact, Contact.AccountId);
        
        // Create opportunity
        Opportunity opp = new Opportunity(
            Name = acc.Name + ' - Initial Opportunity',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        // Register the opportunity relationship
        uow.registerDirty(acc, opp, Opportunity.AccountId);
    }
    // No need to call commitWork() - handled by MetadataTriggerHandler
}
```

## Exception Handling and Logging

### Exception Handling Pattern
- **Always perform try-catches at the Domain Class level**
- **Use Nebula Logger for all logging operations**
- **DO NOT call `Nebula.Logger.saveLogs()` in Domain or Service classes**

The framework automatically calls `Nebula.Logger.saveLogs()` within the MetadataTriggerHandler class. Additional calls can result in duplicate log entries and performance issues.

### Error Handling Example
```apex
public static void updateIndustry(List<Account> accounts) {
    try {
        for (Account acc : accounts) {
            Nebula.Logger.info('Account Object ' + acc);
            if (acc.Industry == null) {
                acc.Industry = 'Media';
            }
        }
    } catch (Exception e) {
        Nebula.Logger.error('Error in updateIndustry: ' + e.getMessage());
    }
}
```

## Critical Requirements (Dos and Don'ts)

### ✅ MUST DO
1. **@namespaceAccessible Annotation**: Always annotate your Object Domain class and its constructor with `@namespaceAccessible`
   ```apex
   @namespaceAccessible
   public with sharing class p1AccountTriggerHandler extends TriggerHandler {
       @namespaceAccessible
       public p1AccountTriggerHandler() {
           // Constructor logic
       }
   }
   ```

2. **Create Metadata Records**: Always create a corresponding `Metadata_Driven_Trigger__mdt` record for your Object Domain Class

3. **Use Consistent Naming Conventions**: Follow the exact naming patterns specified for maintainability

4. **Test in Both Environments**: 
   - Developer Orgs (usually namespaced)
   - QA/UAT/Production Orgs (typically non-namespaced)

5. **Exception Handling**: Always perform try-catches at the Domain Class level

### ❌ MUST NOT DO
1. **DO NOT call `Nebula.Logger.saveLogs()`** in Object Domain Classes or Service Classes - the framework handles this automatically

2. **DO NOT modify existing triggers** in other packages - create new domain classes instead

3. **DO NOT create triggers in higher-level packages** for objects owned by lower-level packages

4. **DO NOT put business logic directly in the trigger file** - use the domain/service pattern

## Governor Limits Awareness
- **SOQL Queries**: Maximum 100 per transaction
- **DML Statements**: Maximum 150 per transaction
- **Heap Size**: 6MB for synchronous, 12MB for asynchronous
- **CPU Time**: 10 seconds for synchronous, 60 seconds for asynchronous

## Testing Guidelines

### Test Class Structure
```apex
@isTest
private class p1AccountTriggerTest {
    
    @TestSetup
    static void setupTestData() {
        // Create test data
    }
    
    @isTest
    static void testBeforeInsert() {
        Test.startTest();
        // Test before insert logic
        Test.stopTest();
        // Assertions
    }
    
    @isTest
    static void testBulkOperations() {
        Test.startTest();
        // Test with 200 records
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Test Account ' + i));
        }
        insert accounts;
        Test.stopTest();
        // Assertions
    }
}
```

## Deployment Considerations

### Environment Context
- **Developer Orgs**: Usually namespaced (due to managed packages)
- **QA Orgs/UAT/Production**: Typically non-namespaced, especially when they mirror production deployment environment
- **Always test in both environments** to avoid namespace resolution issues

### Migration Strategy
- Always backup data before trigger deployment
- Use deployment validation (check-only) first
- Test thoroughly in sandbox environments
- Consider feature flags for gradual rollout

## Anti-Patterns to Avoid

### Common Mistakes
- ❌ SOQL/DML inside loops
- ❌ Hardcoded IDs or values
- ❌ Missing null checks
- ❌ Not handling bulk operations
- ❌ Recursive trigger calls without control
- ❌ Complex business logic directly in trigger

### Performance Issues
- ❌ Inefficient SOQL queries
- ❌ Unnecessary database operations
- ❌ Large collection processing without pagination
- ❌ Missing indexes on frequently queried fields

## Framework Summary

This Metadata-Driven Trigger Framework enables:
- **Single trigger per object** across multiple managed packages
- **Dynamic class loading** through metadata configuration
- **Modular architecture** with clear separation of concerns
- **Built-in features** like bypass API, loop control, and Unit of Work integration
- **Robust error handling** with Nebula Logger integration

Remember: Always follow the package location rules, use proper naming conventions, and leverage the framework's built-in features for optimal performance and maintainability.