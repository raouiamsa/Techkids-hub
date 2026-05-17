const fs = require('fs');
const pdfLib = require('pdf-parse');
const pdf = pdfLib.default || pdfLib;

const filePath = process.argv[2] || 'c:\\Users\\raoui\\OneDrive\\Bureau\\TechKids\\techkids-hub\\pfe (5).pdf';

try {
  const dataBuffer = fs.readFileSync(filePath);
  pdf(dataBuffer).then(function (data) {
    console.log(data.text);
  }).catch(function (error) {
    console.error('Error reading PDF:', error);
  });
} catch (err) {
  console.error('Error opening file:', err.message);
}
