using Microsoft.VisualStudio.TestTools.UnitTesting;
using PayrollSystem;

namespace PayrollSystemTests
{
    [TestClass]
    public class PayrollCalculatorTests
    {
        PayrollCalculator calc = new PayrollCalculator();

        [TestMethod]
        [TestCategory("Gross Pay")]
        public void GrossPayTest()
        {
            double result = calc.CalculateGrossPay(23);

            Assert.AreEqual(21850, result);
        }

        [TestMethod]
        [TestCategory("UIF")]
        public void UIFTest()
        {
            double result = calc.CalculateUIF(21850);

            Assert.AreEqual(218.5, result);
        }

        [TestMethod]
        [TestCategory("Membership")]
        public void MembershipTest()
        {
            double result = calc.CalculateMembership(21850);

            Assert.AreEqual(2840.5, result);
        }

        [TestMethod]
        [TestCategory("PAYE")]
        public void PAYETest()
        {
            double result = calc.CalculatePAYE(21850, 2);

            Assert.AreEqual(4834.3125, result);
        }

        [TestMethod]
        [TestCategory("Net Pay")]
        public void NetPayTest()
        {
            double result =
                calc.CalculateNetPay(
                    21850,
                    218.5,
                    4834.3125,
                    2840.5);

            Assert.AreEqual(13956.6875, result);
        }
    }
}