function generateRandomInvoiceNumber(){
  const characters = '0123456789';
  const length = 8;
  let invoiceNumber = '';

  for (let i = 0; i < length; i++ ){
    const randomIndex = Math.floor(Math.random() * characters.length);
    invoiceNumber += characters[randomIndex];
  }
  return invoiceNumber;
}

var clientsecret = generateRandomInvoiceNumber();

// Set up Stripe.js and Elements to use in checkout form
var style = {
  base: {
    color: "#000",
    lineHeight: '2.4',
    fontSize: '16px'
  }
};

var form = document.getElementById('payment-form');

form.addEventListener('submit', function(ev) {
  ev.preventDefault();

  var custName = document.getElementById("custName").value;
  var phone = document.getElementById("phone").value;
  var custAdd = document.getElementById("custAdd").value;
  var paid = document.getElementById("paid").value;

  // checkbox value (ensure <input id="copy_to_secondary" name="copy_to_secondary"> exists)
  var copyFlag = $('#copy_to_secondary').is(':checked') ? 'on' : 'off';

  // Disable the button and change its text
  var payButton = document.getElementById('submit');
  payButton.disabled = true;
  payButton.textContent = 'Loading...';

  $.ajax({
    type: "POST",
    url: "/orders/add/",               // use relative path
    dataType: "json",
    data: {
      order_number: clientsecret,
      csrfmiddlewaretoken: CSRF_TOKEN,
      productid: $('#submit').val(),
      action: "post",
      cusName: custName,
      phone_num: phone,
      add: custAdd,
      paid: paid,
      copy_to_secondary: copyFlag,     // <-- send checkbox value
    },
    success: function (json) {
      console.log(json.success, 'copied:', json.copy_to_secondary);
      window.location.replace("/payment/orderplaced/");
    },
    error: function (xhr, errmsg, err) {
      payButton.disabled = false;
      payButton.textContent = 'Pay';
      console.error('Order create failed', xhr.responseText || errmsg);
    },
  });
});

