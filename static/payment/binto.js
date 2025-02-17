function showComponent(option) {
    if (option === 'credit') {
      document.getElementById('creditComponent').style.display = 'block';
      document.getElementById('fullPaymentComponent').style.display = 'none';
    } else if (option === 'full') {
      document.getElementById('creditComponent').style.display = 'none';
      document.getElementById('fullPaymentComponent').style.display = 'block';
    }
  }
  
  document.addEventListener('DOMContentLoaded', function() {
    showComponent('full');
});