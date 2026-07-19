import { BookingForm } from "@/components/booking/booking-form";
import { PageHeader } from "@/components/layout/page-header";

export default function BookPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Scheduling"
        title="Book an appointment"
        description="The form builds a natural-language request and sends it to POST /api/v1/reception/message."
      />
      <BookingForm />
    </div>
  );
}
