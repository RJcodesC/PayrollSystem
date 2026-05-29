namespace PayrollSystem
{
    public class PayrollCalculator
    {
        public const double HourlyRate = 950.00;

        public double CalculateGrossPay(double hours)
        {
            return hours * HourlyRate;
        }

        public double CalculateUIF(double grossPay)
        {
            return grossPay * 0.01;
        }

        public double CalculateMembership(double grossPay)
        {
            return grossPay * 0.13;
        }

        public double CalculatePAYE(double grossPay, int dependents)
        {
            return (grossPay - (grossPay * 0.0575 * dependents)) * 0.25;
        }

        public double CalculateNetPay(
            double grossPay,
            double uif,
            double paye,
            double membership)
        {
            return grossPay - uif - paye - membership;
        }
    }
}