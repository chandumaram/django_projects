const addToCart = (productId) => {
    console.log(productId)
  $.ajax({
    type: "POST",
    url: `/cart/add/`,
    headers: {
      "X-CSRFToken": $("input[name=csrfmiddlewaretoken]").val(),
    },
    data: {
      product_id: productId,
      product_qty: 1,
      action: "post",
    },
    success(json) {
      //console.log(json)
      document.getElementById("cart_quantity").textContent = json.qty;
      location.reload();
    },
    error(xhr, errmsg, err) {
      console.log(errmsg);
      console.log(err);
    },
  });
};
