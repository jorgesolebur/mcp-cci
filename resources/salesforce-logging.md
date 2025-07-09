# Salesforce Logging Best Practices - Nebula Logger

## Project Context
This project is focused on developing **2GP (Second Generation Package) Managed Packages** for Salesforce. We leverage **Nebula Logger** as our unified logging framework across all packages to ensure consistent logging practices and centralized log management.

## Overview
Nebula Logger is a comprehensive logging framework built natively on Salesforce using Apex, Lightning Components, and various types of objects. It provides unified logging capabilities across Apex, Lightning Components (LWC & Aura), Flow & Process Builder, creating consolidated logs for better monitoring and debugging.

## Key Features

### Unified Logging Platform
- **Multi-Component Support**: Log entries from Apex, Lightning Components (LWC & Aura), Flow & Process Builder in one consolidated log
- **Centralized Management**: Manage & report on logging data using `Log__c` and `LogEntry__c` objects
- **Real-Time Monitoring**: Leverage `LogEntryEvent__e` platform events for real-time monitoring & integrations
- **User-Level Configuration**: Enable logging and set logging levels for different users & profiles using `LoggerSettings__c` custom hierarchy setting

### Advanced Features
- **Custom Message Formatting**: SystemLogMessageFormat__c uses Handlebars-esque syntax (e.g., `{OriginLocation__c}\n{Message__c}`)
- **Data Masking**: Automatically mask sensitive data using `LogEntryDataMaskRule__mdt` custom metadata rules
- **Related Log Entries**: View related log entries on any Lightning SObject flexipage using the 'Related Log Entries' component
- **Dynamic Tagging**: Assign tags to `Log__c` and `LogEntry__c` records for categorizing and labeling logs
- **Plugin Framework**: Build or install plugins that enhance logging objects using Apex or Flow
- **Event-Driven Integrations**: External integrations can subscribe to log events using `LogEntryEvent__e` platform events

## TH Project Logging Strategy

### Component-Specific Logging Approach

| Component | Debug Logs (On-Demand) | Error Tracking (Default) |
|-----------|-------------------------|-------------------------|
| **Apex Class** | Nebula Logger (Input & output variables and their values for each method) | Nebula Logger (logging exceptions thrown in try/catch) |
| **LWC** | LWC Debug Mode (console.log) + Chrome console | Nebula Logger (logging exceptions thrown in try/catch) |
| **Flow** | Nebula Logger (log flow entry) + Flow Debug | Nebula Logger (logging error message from fault path when performing DML) |

## Architecture Overview

Nebula Logger is built natively on Salesforce with 4 architectural layers:

### 1. Logger Engine Layer
Core logging functionality supporting:
- **Apex**: Full logging capability with multiple log levels
- **Lightning Components**: Both LWC & Aura component logging
- **Flow**: Generic, record-specific, and collection-specific Flow log entries
- **Platform Events**: `LogEntryEvent__e` for real-time event processing

### 2. Log Management Layer
Data management using the Logger Console lightning app:
- **Log__c**: Main log object for transaction-level logging
- **LogEntry__c**: Individual log entries within a transaction
- **LogEntryTag__c**: Junction object for tagging log entries
- **LoggerTag__c**: Tag definition object

### 3. Configuration Layer
Administrative control through:
- **LoggerSettings__c**: User-specific configurations (custom hierarchy setting)
- **LoggerParameter__mdt**: System-wide key-value pair configurations
- **LogEntryDataMaskRule__mdt**: Regex-based data masking rules
- **LogStatus__mdt**: Status mapping for `Log__c.Status__c` to `IsClosed__c` and `IsResolved__c`
- **LogEntryTagRule__mdt**: Automated tagging rules
- **Permission Sets**: LoggerAdmin, LoggerLogViewer, LoggerEndUser, LoggerLogCreator

### 4. Plugin Layer
Extensibility for additional functionality:
- Available for all 5 included objects: `LogEntryEvent__e`, `Log__c`, `LogEntry__c`, `LogEntryTag__c`, `LoggerTag__c`
- Plugin examples: Slack integration, custom dashboards, external monitoring

## Initial Setup & Configuration

### Permission Set Assignment
- **LoggerLogCreator**: Minimum access for generating logs via Apex, Lightning Components, Flow
- **LoggerEndUser**: Log generation + read-only access to shared log records
- **LoggerLogViewer**: View-all access (read-only) to all log records
- **LoggerAdmin**: View-all and modify-all access to all log records

### Customize LoggerSettings__c
Configure settings at org, profile, and user levels for:
- Default logging levels
- Save methods
- Message formatting
- Data retention policies

## Apex Implementation Patterns

### Basic Logging Example
```apex
// This will generate a debug statement within developer console
System.debug('Debug statement using native Apex');

try {
    insert accountList;
} catch (System.DmlException e) {
    // This will create a new `Log__c` record with multiple related `LogEntry__c` records
    for (Integer i = 0; i < e.getNumDml(); i++) {
        // Process exception here
        Logger.error('Message: ' + e.getDmlMessage(i) + ' Stacktrace: ' + e.getStackTraceString());
    }
    Logger.warn('Add log entry using Nebula Logger with logging level == WARN');
    Logger.info('Add log entry using Nebula Logger with logging level == INFO');
    Logger.debug('Add log entry using Nebula Logger with logging level == DEBUG');
    Logger.fine('Add log entry using Nebula Logger with logging level == FINE');
    Logger.finer('Add log entry using Nebula Logger with logging level == FINER');
    Logger.finest('Add log entry using Nebula Logger with logging level == FINEST');
    Logger.saveLog();
} catch (Exception e) {
    // This will create a new `Log__c` record with multiple related `LogEntry__c` records
    Logger.error('Message: ' + e.getMessage() + ' Stacktrace: ' + e.getStackTraceString());
    Logger.saveLog();
}
```

### TH Project Apex Patterns

#### Error Tracking Pattern
Always use try-catches for DML operations and potential errors:

```apex
public with sharing class p1AccountService {
    
    public static void updateAccountIndustry(List<Account> accounts) {
        try {
            // Business logic here
            update accounts;
        } catch (DmlException e) {
            // Log each DML error with context
            for (Integer i = 0; i < e.getNumDml(); i++) {
                Logger.error('DML Error updating account: ' + e.getDmlMessage(i))
                    .setRecord(e.getDmlId(i)); // Link to specific record
            }
            Logger.saveLog();
            throw e; // Re-throw to maintain transaction behavior
        } catch (Exception e) {
            Logger.error('Unexpected error in updateAccountIndustry: ' + e.getMessage())
                .setExceptionDetails(e); // Capture full exception details
            Logger.saveLog();
            throw e;
        }
    }
}
```

#### Debug Logging Pattern
Add debug traces at method entry/exit with input/output values:

```apex
public with sharing class p1AccountService {
    
    public static List<Account> processAccounts(List<Account> inputAccounts) {
        // Method entry logging
        Logger.debug('Entering processAccounts method')
            .addTag('Method Entry')
            .setField('InputCount', inputAccounts.size());
        
        List<Account> processedAccounts = new List<Account>();
        
        try {
            // Business logic here
            for (Account acc : inputAccounts) {
                // Process account
                processedAccounts.add(acc);
            }
            
            // Method exit logging
            Logger.debug('Exiting processAccounts method successfully')
                .addTag('Method Exit')
                .setField('OutputCount', processedAccounts.size());
                
        } catch (Exception e) {
            Logger.error('Error in processAccounts: ' + e.getMessage())
                .setExceptionDetails(e);
            throw e;
        } finally {
            Logger.saveLog();
        }
        
        return processedAccounts;
    }
}
```

### Advanced Apex Features

#### Transaction Controls
```apex
// Suspend saving to reduce DML operations
Logger.suspendSaving();

// Perform multiple operations
Logger.info('First operation');
Logger.info('Second operation');

// Resume and save all at once
Logger.resumeSaving();
Logger.saveLog();
```

#### Different Save Methods
```apex
// Event Bus (default) - uses platform events
Logger.saveLog(Logger.SaveMethod.EVENT_BUS);

// Queueable - asynchronous saving
Logger.saveLog(Logger.SaveMethod.QUEUEABLE);

// REST API - useful for mixed DML scenarios
Logger.saveLog(Logger.SaveMethod.REST);

// Synchronous DML - immediate database insert
Logger.saveLog(Logger.SaveMethod.SYNCHRONOUS_DML);
```

#### Linking Related Transactions
```apex
// In batchable/queueable jobs, link back to original transaction
public class BatchProcessor implements Database.Batchable<SObject> {
    private String originalTransactionId;
    
    public Database.QueryLocator start(Database.BatchableContext context) {
        this.originalTransactionId = Logger.getTransactionId();
        Logger.info('Starting batch process');
        Logger.saveLog();
        return Database.getQueryLocator([SELECT Id FROM Account LIMIT 10]);
    }
    
    public void execute(Database.BatchableContext context, List<Account> scope) {
        Logger.setParentLogTransactionId(this.originalTransactionId);
        Logger.info('Processing batch of ' + scope.size() + ' accounts');
        Logger.saveLog();
    }
}
```

#### Fluent Interface Usage
```apex
// Chain multiple configuration calls
Logger.error('Critical error occurred')
    .setRecord(accountRecord)
    .addTag('Critical')
    .addTag('Production')
    .setField('ErrorCode', 'E001')
    .setExceptionDetails(caughtException);

Logger.saveLog();
```

## Lightning Component Implementation

### LWC Example
```html
<!-- logger-demo.html -->
<template>
    <c-logger></c-logger>
    <div>My component content</div>
</template>
```

```javascript
// logger-demo.js
import { LightningElement } from 'lwc';

export default class LoggerDemo extends LightningElement {
    
    handleOperation() {
        const logger = this.template.querySelector('c-logger');
        
        try {
            // Business logic here
            this.performComplexOperation();
            
            logger.info('Operation completed successfully')
                .addTag('Success');
                
        } catch (error) {
            // TH Pattern: Always log errors in catch blocks
            logger.error('Error in handleOperation: ' + error.message)
                .addTag('Error')
                .setField('ErrorType', error.name);
        } finally {
            logger.saveLog();
        }
    }
    
    performComplexOperation() {
        // Simulate operation that might fail
        throw new Error('Something went wrong');
    }
}
```

### Aura Component Example
```xml
<!-- LoggerDemo.cmp -->
<aura:component implements="force:appHostable">
    <c:logger aura:id="logger" />
    <div>My component content</div>
</aura:component>
```

```javascript
// LoggerDemoController.js
({
    handleOperation: function(component, event, helper) {
        const logger = component.find('logger');
        
        try {
            // Business logic here
            helper.performComplexOperation();
            
            logger.info('Operation completed successfully')
                .addTag('Success');
                
        } catch (error) {
            // TH Pattern: Always log errors in catch blocks
            logger.error('Error in handleOperation: ' + error.message)
                .addTag('Error');
        } finally {
            logger.saveLog();
        }
    }
})
```

## Flow Implementation Patterns

### TH Flow Logging Patterns

#### Debug Pattern - Flow Entry
Add debug logging at the beginning of each Flow with automation details:

**Flow Debug Entry Example:**
- **Action**: Add Log Entry
- **Log Level**: DEBUG
- **Message**: "Account Trigger Flow started - Automations: Update Industry field, Create related Contact, Send notification email"
- **Tags**: "Flow Entry, Account Automation"

#### Error Pattern - Fault Path
Use FAULT path for DML operations to log errors:

**Flow Error Handling Example:**
- **Action**: Add Log Entry (on fault path)
- **Log Level**: ERROR
- **Message**: "Failed to update Account Industry: {!$Flow.FaultMessage}"
- **Record**: {!$Record} (the account record that failed)
- **Tags**: "DML Error, Account Update"

### Flow Actions Available

1. **Add Log Entry** - Basic message logging
2. **Add Log Entry for an SObject Record** - Log with record context
3. **Add Log Entry for an SObject Record Collection** - Log with collection context
4. **Save Log** - Persist all pending log entries

### Flow Tagging Example
Use comma-separated tags in the Tags field:
```
"Flow Entry, Account Automation, Critical Process"
```

## Advanced Features

### Dynamic Tagging

#### Apex Tagging
```apex
// Add single tag
Logger.debug('Processing account').addTag('Account Processing');

// Add multiple tags
List<String> tags = new List<String>{'Critical', 'Production', 'Account'};
Logger.error('Account update failed').addTags(tags);
```

#### Metadata-Based Tagging
Configure `LogEntryTagRule__mdt` records to automatically apply tags:

- **Logger SObject**: Log Entry
- **Field**: LogEntry__c.Message__c
- **Comparison Type**: CONTAINS
- **Comparison Value**: "Account update failed"
- **Tags**: "Critical Error\nAccount Processing"
- **Is Enabled**: true

### Log Management Features

#### Logger Console App
- Access to all Logger objects: `Log__c`, `LogEntry__c`, `LogEntryTag__c`, `LoggerTag__c`
- Real-time monitoring via Log Entry Event Stream
- Filtering and search capabilities

#### Log Quick Actions
- **Manage Log**: Update owner, priority, and status
- **View JSON**: See complete log in JSON format with clipboard copy

#### Related Log Entries Component
Add to any Lightning record page to show related log entries:
- Automatic filtering by `LogEntry__c.RecordId__c`
- Built-in search functionality
- Respects Salesforce security model

### Data Retention & Cleanup

#### Automatic Cleanup
```apex
// LogBatchPurger - deletes logs where Log__c.LogRetentionDate__c <= System.today()
// Default retention: TODAY + 14 days (configurable in LoggerSettings__c)

// Schedule automatic cleanup
LogBatchPurgeScheduler scheduler = new LogBatchPurgeScheduler();
System.schedule('Daily Log Cleanup', '0 0 2 * * ?', scheduler);
```

#### Manual Cleanup
- Mass delete via list view custom button
- Individual record deletion
- Bulk operations via Data Loader

## Security & Best Practices

### Data Masking
Configure `LogEntryDataMaskRule__mdt` to automatically mask sensitive data:
- SSN patterns: `\d{3}-\d{2}-\d{4}`
- Credit card patterns: `\d{4}-\d{4}-\d{4}-\d{4}`
- Custom patterns for your org's sensitive data

### Permission Management
- Use appropriate permission sets for different user roles
- Leverage record-level security for sensitive logs
- Configure field-level security for log entry fields

### Performance Considerations
- Use appropriate save methods based on context
- Consider `Logger.suspendSaving()` for high-volume operations
- Monitor log volume and adjust retention policies

## Anti-Patterns to Avoid

### ❌ Don't Do This
- **System.debug() in production code** - Use Nebula Logger instead
- **Logging sensitive data** - Configure masking rules
- **Excessive logging in loops** - Use bulk logging patterns
- **Ignoring log levels** - Configure appropriate levels per environment
- **Manual log deletion** - Use automated cleanup jobs

### ✅ Do This Instead
- **Use Nebula Logger consistently** across all components
- **Configure appropriate log levels** for different environments
- **Implement proper error handling** with contextual logging
- **Use tagging strategically** for log organization
- **Set up automated monitoring** for critical errors

## Environment-Specific Configuration

### Development
- **Log Level**: DEBUG or FINE
- **Retention**: 7 days
- **Save Method**: EVENT_BUS

### QA/UAT
- **Log Level**: INFO
- **Retention**: 14 days
- **Save Method**: EVENT_BUS

### Production
- **Log Level**: WARN or ERROR
- **Retention**: 30 days
- **Save Method**: QUEUEABLE (for performance)

## Summary

Nebula Logger provides a comprehensive, unified logging solution for our 2GP managed package development. By following these patterns and leveraging the framework's advanced features, we ensure consistent, maintainable, and secure logging across all components of our Salesforce solutions.

Remember: Consistent logging practices are essential for debugging, monitoring, and maintaining production applications. Always use appropriate log levels, implement proper error handling, and leverage the framework's built-in features for optimal performance and security.