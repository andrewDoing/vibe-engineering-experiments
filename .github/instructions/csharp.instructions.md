---
applyTo: "*.cs, *.csproj, *.sln, *.razor, *.cshtml"
---
# Use C# 12 features

- Use Primary Constructor Syntax
```csharp
public class UserManager(
    ILogger<UserManager> logger,
    IConfiguration configuration,
    IdentityDbContext dbContext)
{
    // Class members can directly use logger, configuration, and dbContext
}
```

- Use is null for null checks to ensure consistent and predictable behavior.
```csharp
if (user is null)
{
    throw new ArgumentNullException(nameof(user));
}
```

- Use collection expressions with []
```csharp
var numbers = [1, 2, 3];
```

- use new() for object initialization
```csharp
List<int> numbers = new();
```

## Additional Guidelines
- Prefer using `var` for local variable declarations when the type is evident from the right side of the assignment.
- Prefer Prefer IsSuccessStatusCode Over EnsureSuccessStatusCode() for HTTP responses
- Default to LogDebug for logging over LogInformation for new code, but don't change existing logs.