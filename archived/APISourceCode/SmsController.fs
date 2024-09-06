// SmsController.fs

namespace ConTXT.Controllers

open Microsoft.AspNetCore.Mvc
open System
open ConTXT.Data
open Microsoft.EntityFrameworkCore
open System.Threading.Tasks
open System.Linq
open Microsoft.FSharp.Core

[<ApiController>]
[<Route("api/[controller]")>]
type SmsController(context: ConTXTContext) =
    inherit ControllerBase()

    // Helper function to normalize phone numbers
    let normalizePhoneNumber (phoneNumber: string) : string =
        new string(phoneNumber.ToCharArray() |> Array.filter Char.IsDigit)

    // Helper function to create a LIKE pattern
    let createLikePattern (phoneNumber: string) : string =
        let digits = normalizePhoneNumber phoneNumber
        "%" + String.Join("%", digits.ToCharArray()) + "%"

    [<HttpPost>]
    member this.ReceiveSms([<FromBody>] payload: SmsPayload) : Task<IActionResult> =
        task {
            let normalizedIncomingNumber = normalizePhoneNumber payload.FromNumber
            let likePattern = createLikePattern payload.FromNumber

            let! potentialMatches = 
                context.Contacts
                    .Where(fun c -> EF.Functions.Like(c.PhoneNumber, likePattern))
                    .ToListAsync()

            let contact = 
                potentialMatches 
                |> Seq.tryFind (fun c -> normalizePhoneNumber c.PhoneNumber = normalizedIncomingNumber)

            match contact with
            | None -> 
                return this.BadRequest("No matching contact found for the given phone number") :> IActionResult
            | Some contact ->
                // Check for matching TextID in the database, get the most recent
                let! matchingSms = 
                    context.SMS
                        .Where(fun s -> s.TextID = payload.TextId)
                        .OrderByDescending(fun s -> s.DateTime)  // Sort by DateTime in descending order
                        .FirstOrDefaultAsync()

                let emailId = 
                    if isNull (box matchingSms) then 0
                    else matchingSms.EmailID

                let sms = Sms()
                sms.ContactID <- contact.ContactID
                sms.Message <- payload.Text
                sms.Status <- "Delivered"
                sms.DateTime <- DateTime.Now
                sms.TextID <- payload.TextId
                sms.Number <- payload.FromNumber
                sms.Direction <- "Inbound"
                sms.Processed <- 'N'
                sms.EmailID <- emailId  // Use the EmailID from the most recent matching SMS, or 0 if not found

                context.SMS.Add(sms) |> ignore
                try
                    do! context.SaveChangesAsync() |> Async.AwaitTask |> Async.Ignore
                    return this.Ok(sprintf "SMS received and logged successfully for contact: %s. EmailID: %d" contact.ContactName emailId) :> IActionResult
                with
                | ex ->
                    // Log the exception
                    return this.StatusCode(500, "An error occurred while processing the SMS") :> IActionResult
        }

    [<HttpGet("test")>]
    member this.Test() : IActionResult = 
        this.Ok("API is working") :> IActionResult

and SmsPayload = {
    TextId: string
    FromNumber: string
    Text: string
}