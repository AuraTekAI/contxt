// Program.fs

open System
open Microsoft.AspNetCore.Builder
open Microsoft.Extensions.DependencyInjection
open Microsoft.Extensions.Hosting
open Microsoft.EntityFrameworkCore
open ConTXT.Data
open Microsoft.Extensions.Configuration
open Microsoft.Extensions.Logging
open Microsoft.OpenApi.Models
open Microsoft.AspNetCore.Mvc.Infrastructure

[<EntryPoint>]
let main args =
    let builder = WebApplication.CreateBuilder(args)
    
    // Add services to the container
    builder.Services.AddControllers() |> ignore
    builder.Services.AddDbContext<ConTXTContext>(fun options ->
        options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection"))
        |> ignore
    ) |> ignore
    
    // Add Swagger only in Development environment
    if builder.Environment.IsDevelopment() then
        builder.Services.AddEndpointsApiExplorer() |> ignore
        builder.Services.AddSwaggerGen(fun c ->
            c.SwaggerDoc("v1", OpenApiInfo(Title = "SMS Receiver API", Version = "v1"))
        ) |> ignore
    
    // Build the application
    let app = builder.Build()
    
    app.Logger.LogInformation("Application starting up")
    
    // Configure the HTTP request pipeline
    if app.Environment.IsDevelopment() then
        app.UseSwagger() |> ignore
        app.UseSwaggerUI(fun c ->
            c.SwaggerEndpoint("/swagger/v1/swagger.json", "SMS Receiver API V1")
        ) |> ignore
    
    app.UseHttpsRedirection() |> ignore
    app.UseAuthorization() |> ignore
    app.MapControllers() |> ignore
    
    app.Logger.LogInformation("Controllers mapped")
    
    // Log route information (you can keep or remove this based on your needs)
    let actionDescriptorCollectionProvider = app.Services.GetService<IActionDescriptorCollectionProvider>()
    if actionDescriptorCollectionProvider <> null then
        let routes = actionDescriptorCollectionProvider.ActionDescriptors.Items
        for route in routes do
            let controllerName = route.RouteValues.["controller"]
            let actionName = route.RouteValues.["action"]
            let httpMethods = String.Join(", ", route.ActionConstraints |> Seq.choose (function :? Microsoft.AspNetCore.Mvc.ActionConstraints.HttpMethodActionConstraint as c -> Some (String.Join(", ", c.HttpMethods)) | _ -> None))
            app.Logger.LogInformation(sprintf "Controller: %s, Action: %s, HTTP Methods: %s" controllerName actionName httpMethods)
    
    app.Run()
    
    0 // Exit code