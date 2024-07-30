// ConTXTContext.fs

namespace ConTXT.Data

open System
open System.ComponentModel.DataAnnotations
open Microsoft.EntityFrameworkCore

type Contact() =
    member val ContactID : int = 0 with get, set
    member val UserID : int = 0 with get, set
    member val ContactName : string = "" with get, set
    member val PhoneNumber : string = "" with get, set
    member val EmailAddress : string = "" with get, set

type Sms() =
    member val SMSID : int = 0 with get, set
    member val ContactID : int = 0 with get, set
    member val Message : string = "" with get, set
    member val Status : string = "" with get, set
    member val DateTime : DateTime = DateTime.MinValue with get, set
    member val TextID : string = "" with get, set
    member val Number : string = "" with get, set
    member val Direction : string = "" with get, set
    member val Processed : char = 'N' with get, set
    member val EmailID : int = 0 with get, set

type ConTXTContext(options: DbContextOptions<ConTXTContext>) =
    inherit DbContext(options)

    [<DefaultValue>]
    val mutable sms : DbSet<Sms>
    member this.SMS with get() = this.sms and set v = this.sms <- v
    
    [<DefaultValue>]
    val mutable contacts : DbSet<Contact>
    member this.Contacts with get() = this.contacts and set v = this.contacts <- v

    override this.OnModelCreating(modelBuilder: ModelBuilder) =
        modelBuilder.Entity<Sms>().ToTable("SMS") |> ignore